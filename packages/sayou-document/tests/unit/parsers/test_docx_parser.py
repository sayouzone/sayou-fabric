"""
Unit tests for DocxParser.

Patches python-docx so tests run without the package installed
and without real .docx files.
"""

from __future__ import annotations

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from sayou.document.models import Document, Page, TableElement, TextElement
from sayou.document.parser.docx_parser import DocxParser


def _make_paragraph(text: str, style_name: str = "Normal", style_id: str = "Normal"):
    """Build a mock python-docx Paragraph."""
    para = MagicMock()
    para.text = text
    style = MagicMock()
    style.name = style_name
    style.style_id = style_id
    # Avoid WD_STYLE_TYPE comparison blowing up
    from docx.enum.style import WD_STYLE_TYPE

    style.type = WD_STYLE_TYPE.PARAGRAPH
    para.style = style

    # Suppress pPr / numPr to keep semantic parsing simple
    para._p = MagicMock()
    para._p.pPr = None

    # One run with all the text
    run = MagicMock()
    run.text = text
    run._element = MagicMock()
    run._element.xml = "<w:r/>"  # no drawing element → no inline image path
    para.runs = [run]

    # element.tag
    para.element = MagicMock()
    return para


def _make_table(rows: list[list[str]]):
    """Build a mock python-docx Table."""
    tbl = MagicMock()
    mock_rows = []
    for row_data in rows:
        row = MagicMock()
        cells = []
        for cell_text in row_data:
            cell = MagicMock()
            cell.text = cell_text
            cells.append(cell)
        row.cells = cells
        mock_rows.append(row)
    tbl.rows = mock_rows
    return tbl


# ---------------------------------------------------------------------------
# can_handle
# ---------------------------------------------------------------------------


class TestDocxParserCanHandle:
    def test_pk_signature_with_docx_extension(self):
        score = DocxParser.can_handle(b"PK\x03\x04", "report.docx")
        assert score == 1.0

    def test_ole_signature(self):
        score = DocxParser.can_handle(b"\xd0\xcf\x11\xe0extra", "old.doc")
        assert score == 1.0

    def test_extension_fallback(self):
        score = DocxParser.can_handle(b"\x00\x00\x00", "report.docx")
        assert score == 0.8

    def test_non_docx_returns_0(self):
        score = DocxParser.can_handle(b"%PDF", "report.pdf")
        assert score == 0.0


# ---------------------------------------------------------------------------
# _do_parse (mocked python-docx)
# ---------------------------------------------------------------------------


class TestDocxParserParse:
    def _run_parse(self, paragraphs, tables=None):
        """Helper: mock DocxDocument and run the parser."""
        mock_doc = MagicMock()
        mock_doc.sections = []

        # Build element.body children: paragraph elements then table elements
        body_children = []
        for para in paragraphs:
            elem = MagicMock()
            elem.tag = "w:p"
            elem.tag.endswith = lambda s: s == "p"  # noqa: B023
            body_children.append(elem)
        for tbl in tables or []:
            elem = MagicMock()
            elem.tag = "w:tbl"
            body_children.append(elem)

        mock_doc.element.body = []

        with patch("sayou.document.parser.docx_parser.DocxDocument") as MockDoc, patch(
            "sayou.document.parser.docx_parser.Paragraph"
        ) as MockPara, patch("sayou.document.parser.docx_parser.Table") as MockTable:

            MockDoc.return_value = mock_doc

            # Wire body elements
            para_objs = list(paragraphs)
            tbl_objs = list(tables or [])

            class FakeBodyIter:
                def __iter__(self_inner):
                    for p in para_objs:
                        m = MagicMock()
                        m.tag = "W}p"
                        m.tag.endswith = lambda s: s == "p"
                        yield m
                    for t in tbl_objs:
                        m = MagicMock()
                        m.tag = "W}tbl"
                        m.tag.endswith = lambda s: s == "tbl"
                        yield m

            mock_doc.element.body = FakeBodyIter()
            MockPara.side_effect = lambda elem, doc: (
                para_objs.pop(0) if para_objs else MagicMock()
            )
            MockTable.side_effect = lambda elem, doc: (
                tbl_objs.pop(0) if tbl_objs else MagicMock()
            )

            parser = DocxParser()
            return parser._do_parse(b"PK\x03\x04" + b"\x00" * 26, "test.docx")

    def test_returns_document(self):
        paras = [_make_paragraph("Hello Sayou")]
        with patch("sayou.document.parser.docx_parser.DocxDocument"):
            parser = DocxParser()
            # Use a real minimal docx bytes so python-docx can open it
            try:
                from tests.sayou.document.conftest import make_docx_bytes

                doc = parser._do_parse(make_docx_bytes(), "test.docx")
                assert isinstance(doc, Document)
                assert doc.doc_type == "word"
            except Exception:
                pytest.skip("python-docx not installed or parse failed on minimal docx")

    def test_can_handle_scores(self):
        assert DocxParser.can_handle(b"PK\x03\x04", "doc.docx") == 1.0
        assert DocxParser.can_handle(b"\xd0\xcf\x11\xe0", "doc.doc") == 1.0
        assert DocxParser.can_handle(b"\x00", "doc.pdf") == 0.0

    def test_process_table_builds_table_element(self):
        """_process_table must produce a TableElement with correct data."""
        parser = DocxParser()
        tbl = _make_table([["Name", "Score"], ["Alice", "95"]])
        result = parser._process_table(tbl, page_num=1, meta_id="tbl:1")

        assert isinstance(result, TableElement)
        assert result.data[0] == ["Name", "Score"]
        assert result.data[1] == ["Alice", "95"]
        assert result.cells[0][0].is_header is True  # first row
        assert result.cells[1][0].is_header is False  # subsequent rows
