"""
Unit tests for RefineryPipeline.

Covers:
- _register_manual routing (Bug #14 regression)
- _resolve_normalizer strategy dispatch
- run() normalization + processor chain
- process() facade
- ALL processor mode
- Empty input handling
"""

from __future__ import annotations

import logging
from typing import Any, List
from unittest.mock import MagicMock, patch

import pytest
from sayou.core.schemas import SayouBlock

from sayou.refinery.core.exceptions import RefineryError
from sayou.refinery.interfaces.base_normalizer import BaseNormalizer
from sayou.refinery.interfaces.base_processor import BaseProcessor
from sayou.refinery.pipeline import RefineryPipeline

# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------


class _TextNormalizer(BaseNormalizer):
    component_name = "TextNormalizer"

    @classmethod
    def can_handle(cls, raw_data, strategy="auto"):
        return 1.0 if isinstance(raw_data, str) else 0.0

    def _do_normalize(self, raw_data):
        return [SayouBlock(type="text", content=raw_data, metadata={})]


class _DictNormalizer(BaseNormalizer):
    component_name = "DictNormalizer"

    @classmethod
    def can_handle(cls, raw_data, strategy="auto"):
        return 1.0 if isinstance(raw_data, dict) else 0.0

    def _do_normalize(self, raw_data):
        return [SayouBlock(type="record", content=raw_data, metadata={})]


class _UpperCaseProcessor(BaseProcessor):
    component_name = "UpperCaseProcessor"

    def _do_process(self, blocks):
        for b in blocks:
            if isinstance(b.content, str):
                b.content = b.content.upper()
        return blocks


class _NullProcessor(BaseProcessor):
    component_name = "NullProcessor"

    def _do_process(self, blocks):
        return []


# ---------------------------------------------------------------------------
# Helper: pipeline without auto-discovery
# ---------------------------------------------------------------------------


def _bare_pipeline(**kwargs):
    with patch.object(RefineryPipeline, "_register"), patch.object(
        RefineryPipeline, "_load_from_registry"
    ), patch.object(RefineryPipeline, "initialize"):
        p = RefineryPipeline.__new__(RefineryPipeline)
        p.normalizer_cls_map = {}
        p.processor_cls_map = {}
        p._callbacks = []
        p.global_config = {}
        p.logger = logging.getLogger("RefineryPipeline")  # ← 추가
    return p


# ---------------------------------------------------------------------------
# _register_manual (Bug #14 regression)
# ---------------------------------------------------------------------------


class TestRegisterManual:
    def test_normalizer_goes_to_normalizer_map(self):
        p = _bare_pipeline()
        p._register_manual(_TextNormalizer)
        assert "TextNormalizer" in p.normalizer_cls_map
        assert "TextNormalizer" not in p.processor_cls_map

    def test_processor_goes_to_processor_map(self):
        p = _bare_pipeline()
        p._register_manual(_UpperCaseProcessor)
        assert "UpperCaseProcessor" in p.processor_cls_map
        assert "UpperCaseProcessor" not in p.normalizer_cls_map

    def test_non_type_raises_type_error(self):
        p = _bare_pipeline()
        with pytest.raises(TypeError):
            p._register_manual("not_a_class")

    def test_both_maps_stay_separate(self):
        """Before the fix, both maps received every registered class."""
        p = _bare_pipeline()
        p._register_manual(_TextNormalizer)
        p._register_manual(_UpperCaseProcessor)
        assert len(p.normalizer_cls_map) == 1
        assert len(p.processor_cls_map) == 1


# ---------------------------------------------------------------------------
# _resolve_normalizer
# ---------------------------------------------------------------------------


class TestResolveNormalizer:
    def test_explicit_strategy_key(self):
        p = _bare_pipeline()
        p.normalizer_cls_map = {"TextNormalizer": _TextNormalizer}
        cls = p._resolve_normalizer("hello", "TextNormalizer")
        assert cls is _TextNormalizer

    def test_auto_selects_best_score(self):
        p = _bare_pipeline()
        p.normalizer_cls_map = {
            "TextNormalizer": _TextNormalizer,
            "DictNormalizer": _DictNormalizer,
        }
        cls = p._resolve_normalizer({"key": "val"}, "auto")
        assert cls is _DictNormalizer

    def test_returns_none_when_no_match(self):
        p = _bare_pipeline()
        p.normalizer_cls_map = {}
        result = p._resolve_normalizer("data", "auto")
        assert result is None


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------


class TestRefineryPipelineRun:
    def _pipeline(self, normalizers=None, processors=None):
        p = _bare_pipeline()
        p.normalizer_cls_map = {c.component_name: c for c in (normalizers or [])}
        p.processor_cls_map = {c.component_name: c for c in (processors or [])}
        return p

    def test_basic_normalization(self):
        p = self._pipeline(normalizers=[_TextNormalizer])
        blocks = p.run("hello world")
        assert len(blocks) == 1
        assert blocks[0].content == "hello world"

    def test_processor_applied(self):
        p = self._pipeline(
            normalizers=[_TextNormalizer],
            processors=[_UpperCaseProcessor],
        )
        blocks = p.run("hello", processors=["UpperCaseProcessor"])
        assert blocks[0].content == "HELLO"

    def test_unknown_processor_skipped_gracefully(self):
        p = self._pipeline(normalizers=[_TextNormalizer])
        # Should not raise — unknown processor is warned and skipped
        blocks = p.run("data", processors=["NonExistentProcessor"])
        assert len(blocks) == 1

    def test_no_processors_returns_normalized_blocks(self):
        p = self._pipeline(normalizers=[_TextNormalizer])
        blocks = p.run("data", processors=[])
        assert blocks[0].content == "data"

    def test_none_input_returns_empty_list(self):
        p = self._pipeline(normalizers=[_TextNormalizer])
        result = p.run(None)
        assert result == []

    def test_raises_refinery_error_when_no_normalizer(self):
        p = self._pipeline()
        with pytest.raises(RefineryError):
            p.run("data")

    def test_all_processors_mode(self):
        p = self._pipeline(
            normalizers=[_TextNormalizer],
            processors=[_NullProcessor],
        )
        blocks = p.run("data", processors="ALL")
        # NullProcessor returns empty list
        assert blocks == []

    def test_callbacks_forwarded(self):
        p = self._pipeline(normalizers=[_TextNormalizer])
        cb = MagicMock()
        p._callbacks = [cb]
        p.run("hello")
        # Just verify run completes without AttributeError

    def test_run_config_merges_global_and_runtime(self):
        p = self._pipeline(normalizers=[_TextNormalizer])
        p.global_config = {"setting": "global"}
        # Should not crash — run_config merges correctly
        blocks = p.run("data", extra_option="runtime")
        assert len(blocks) == 1


# ---------------------------------------------------------------------------
# process() facade
# ---------------------------------------------------------------------------


class TestRefineryPipelineProcess:
    def test_process_is_facade_for_run(self):
        with patch.object(
            RefineryPipeline, "__init__", lambda *a, **k: None
        ), patch.object(RefineryPipeline, "run") as mock_run:
            mock_run.return_value = [SayouBlock(type="text", content="x", metadata={})]
            RefineryPipeline.process.__func__(RefineryPipeline, "data")
            mock_run.assert_called_once()
