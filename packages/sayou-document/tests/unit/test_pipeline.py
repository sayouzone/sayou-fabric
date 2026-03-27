"""
Unit tests for DocumentPipeline.

Covers:
- _register_manual routing (Bug #5 regression)
- _resolve_component score selection
- run() orchestration with mocked parsers
- process() facade
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sayou.document.core.exceptions import ParserError
from sayou.document.interfaces.base_converter import BaseConverter
from sayou.document.interfaces.base_ocr import BaseOCR
from sayou.document.interfaces.base_parser import BaseDocumentParser
from sayou.document.models import Document, Page
from sayou.document.pipeline import DocumentPipeline


# ---------------------------------------------------------------------------
# Minimal stubs
# ---------------------------------------------------------------------------


class _FakeParser(BaseDocumentParser):
    component_name = "FakeParser"
    SUPPORTED_TYPES = [".fake"]

    @classmethod
    def can_handle(cls, file_bytes, file_name):
        return 1.0 if file_name.endswith(".fake") else 0.0

    def _do_parse(self, file_bytes, file_name, **kwargs):
        return Document(
            file_name=file_name,
            file_id=file_name,
            doc_type="pdf",
            page_count=1,
            pages=[Page(page_num=1)],
        )


class _FakeConverter(BaseConverter):
    component_name = "FakeConverter"
    SUPPORTED_TYPES = [".img"]

    def _do_convert(self, file_bytes, file_name, **kwargs):
        return b"%PDF-converted"


class _FakeOCR(BaseOCR):
    component_name = "FakeOCR"

    def _do_ocr(self, image_bytes, **kwargs):
        return "ocr result"


# ---------------------------------------------------------------------------
# _register_manual (Bug #5 regression)
# ---------------------------------------------------------------------------


class TestRegisterManual:
    def _make_pipeline(self):
        with patch.object(DocumentPipeline, "_register"), patch.object(
            DocumentPipeline, "_load_from_registry"
        ):
            p = DocumentPipeline.__new__(DocumentPipeline)
            p.converter_cls_map = {}
            p.ocr_cls_map = {}
            p.parser_cls_map = {}
            p._callbacks = []
            p.global_config = {}
            return p

    def test_parser_goes_to_parser_map(self):
        p = self._make_pipeline()
        p._register_manual(_FakeParser)
        assert "FakeParser" in p.parser_cls_map
        assert "FakeParser" not in p.converter_cls_map
        assert "FakeParser" not in p.ocr_cls_map

    def test_ocr_goes_to_ocr_map(self):
        p = self._make_pipeline()
        p._register_manual(_FakeOCR)
        assert "FakeOCR" in p.ocr_cls_map
        assert "FakeOCR" not in p.parser_cls_map

    def test_converter_goes_to_converter_map(self):
        p = self._make_pipeline()
        p._register_manual(_FakeConverter)
        assert "FakeConverter" in p.converter_cls_map
        assert "FakeConverter" not in p.parser_cls_map

    def test_non_type_raises_type_error(self):
        p = self._make_pipeline()
        with pytest.raises(TypeError):
            p._register_manual("not_a_class")


# ---------------------------------------------------------------------------
# _resolve_component
# ---------------------------------------------------------------------------


class TestResolveComponent:
    def _make_pipeline(self):
        with patch.object(DocumentPipeline, "_register"), patch.object(
            DocumentPipeline, "_load_from_registry"
        ):
            p = DocumentPipeline.__new__(DocumentPipeline)
            p.converter_cls_map = {}
            p.ocr_cls_map = {}
            p.parser_cls_map = {}
            p._callbacks = []
            p.global_config = {}
            return p

    def test_selects_highest_scorer(self):
        class LowParser(BaseDocumentParser):
            component_name = "Low"

            @classmethod
            def can_handle(cls, b, n):
                return 0.3

            def _do_parse(self, b, n, **k):
                pass

        class HighParser(BaseDocumentParser):
            component_name = "High"

            @classmethod
            def can_handle(cls, b, n):
                return 0.9

            def _do_parse(self, b, n, **k):
                pass

        p = self._make_pipeline()
        cls_map = {"Low": LowParser, "High": HighParser}
        selected = p._resolve_component(cls_map, b"data", "doc.txt", "Parser")
        assert selected is HighParser

    def test_returns_none_when_all_score_zero(self):
        class ZeroParser(BaseDocumentParser):
            component_name = "Zero"

            @classmethod
            def can_handle(cls, b, n):
                return 0.0

            def _do_parse(self, b, n, **k):
                pass

        p = self._make_pipeline()
        result = p._resolve_component({"Zero": ZeroParser}, b"", "x.txt", "P")
        assert result is None


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------


class TestDocumentPipelineRun:
    def _pipeline_with_parser(self, parser_cls):
        with patch.object(DocumentPipeline, "_register"), patch.object(
            DocumentPipeline, "_load_from_registry"
        ), patch.object(DocumentPipeline, "initialize"):
            p = DocumentPipeline.__new__(DocumentPipeline)
            p.converter_cls_map = {}
            p.ocr_cls_map = {}
            p.parser_cls_map = {parser_cls.component_name: parser_cls}
            p._callbacks = []
            p.global_config = {}
        return p

    def test_run_returns_document(self):
        pipeline = self._pipeline_with_parser(_FakeParser)
        doc = pipeline.run(b"fake content", "report.fake")
        assert isinstance(doc, Document)

    def test_run_raises_parser_error_for_unknown_type(self):
        pipeline = self._pipeline_with_parser(_FakeParser)
        with pytest.raises(ParserError):
            pipeline.run(b"data", "unknown.xyz")

    def test_run_raises_on_empty_bytes(self):
        pipeline = self._pipeline_with_parser(_FakeParser)
        with pytest.raises(ParserError):
            pipeline.run(b"", "report.fake")

    def test_callbacks_forwarded_to_parser(self):
        """_callbacks must be passed to the parser instance without hasattr guard."""
        pipeline = self._pipeline_with_parser(_FakeParser)
        cb = MagicMock()
        pipeline._callbacks = [cb]
        pipeline.run(b"fake content", "doc.fake")
        # add_callback on _FakeParser instances is inherited from BaseComponent
        # We just verify run() completes without AttributeError


# ---------------------------------------------------------------------------
# process() facade
# ---------------------------------------------------------------------------


class TestDocumentPipelineProcess:
    def test_process_facade(self):
        with patch.object(DocumentPipeline, "run") as mock_run:
            mock_run.return_value = Document(
                file_name="f.fake", file_id="f", doc_type="pdf"
            )
            with patch.object(DocumentPipeline, "__init__", lambda *a, **k: None):
                result = DocumentPipeline.process.__func__(
                    DocumentPipeline, b"bytes", "f.fake"
                )
