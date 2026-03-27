"""
Unit tests for PdfParser.

Uses unittest.mock to patch fitz so the tests run without PyMuPDF installed
and without actual PDF files on disk.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sayou.document.models import Document, ImageElement, Page, TextElement
from sayou.document.parser.pdf_parser import PdfParser


def _make_fitz_page(
    text: str = "Sample page text.",
    blocks: list | None = None,
    width: float = 612.0,
    height: float = 792.0,
):
    """Build a minimal fitz page mock."""
    page = MagicMock()
    page.rect.width = width
    page.rect.height = height
    page.get_text.return_value = text

    default_blocks = [
        {
            "type": 0,
            "number": 0,
            "bbox": (10, 10, 200, 30),
            "lines": [{"spans": [{"text": text}]}],
        }
    ]
    page.get_text.side_effect = lambda *args, **kwargs: (
        {"blocks": blocks if blocks is not None else default_blocks}
        if args and args[0] == "dict"
        else text
    )
    return page


def _make_fitz_doc(pages=None):
    """Build a minimal fitz Document mock."""
    doc = MagicMock()
    pages = pages or [_make_fitz_page()]
    doc.page_count = len(pages)
    doc.load_page.side_effect = lambda i: pages[i]
    doc.get_toc.return_value = [[1, "Introduction", 1]]
    return doc


# ---------------------------------------------------------------------------
# can_handle
# ---------------------------------------------------------------------------


class TestPdfParserCanHandle:
    def test_pdf_magic_bytes_returns_1(self):
        assert PdfParser.can_handle(b"%PDF-1.4 content", "report.pdf") == 1.0

    def test_pdf_extension_fallback(self):
        assert PdfParser.can_handle(b"\x00\x00\x00", "report.pdf") == 0.8

    def test_non_pdf_returns_0(self):
        assert PdfParser.can_handle(b"\x00\x00\x00", "report.docx") == 0.0

    def test_empty_bytes_with_extension(self):
        score = PdfParser.can_handle(b"", "doc.pdf")
        assert score >= 0.0


# ---------------------------------------------------------------------------
# _do_parse (mocked fitz)
# ---------------------------------------------------------------------------


class TestPdfParserParse:
    @patch("sayou.document.parser.pdf_parser.fitz")
    def test_returns_document_object(self, mock_fitz):
        mock_fitz.open.return_value = _make_fitz_doc()
        mock_fitz.TEXTFLAGS_DICT = 0

        parser = PdfParser()
        doc = parser._do_parse(b"%PDF-fake", "test.pdf")

        assert isinstance(doc, Document)
        assert doc.doc_type == "pdf"
        assert doc.file_name == "test.pdf"

    @patch("sayou.document.parser.pdf_parser.fitz")
    def test_page_count_matches(self, mock_fitz):
        pages = [_make_fitz_page(f"Page {i}") for i in range(3)]
        mock_fitz.open.return_value = _make_fitz_doc(pages)
        mock_fitz.TEXTFLAGS_DICT = 0

        parser = PdfParser()
        doc = parser._do_parse(b"%PDF-fake", "multi.pdf")

        assert doc.page_count == 3
        assert len(doc.pages) == 3

    @patch("sayou.document.parser.pdf_parser.fitz")
    def test_text_element_content_preserved(self, mock_fitz):
        """Regression: TextElement.text must survive the full parse path."""
        mock_fitz.open.return_value = _make_fitz_doc()
        mock_fitz.TEXTFLAGS_DICT = 0

        parser = PdfParser()
        doc = parser._do_parse(b"%PDF-fake", "text.pdf")

        text_elems = [e for e in doc.pages[0].elements if isinstance(e, TextElement)]
        assert len(text_elems) > 0
        assert text_elems[0].text != ""

    @patch("sayou.document.parser.pdf_parser.fitz")
    def test_toc_extracted(self, mock_fitz):
        mock_fitz.open.return_value = _make_fitz_doc()
        mock_fitz.TEXTFLAGS_DICT = 0

        parser = PdfParser()
        doc = parser._do_parse(b"%PDF-fake", "toc.pdf")

        assert len(doc.toc) == 1
        assert doc.toc[0]["title"] == "Introduction"

    @patch("sayou.document.parser.pdf_parser.fitz")
    def test_empty_text_page_does_not_crash(self, mock_fitz):
        """A page with no text blocks should produce a Page with no elements."""
        page = _make_fitz_page(text="", blocks=[])
        mock_fitz.open.return_value = _make_fitz_doc([page])
        mock_fitz.TEXTFLAGS_DICT = 0

        parser = PdfParser()
        doc = parser._do_parse(b"%PDF-fake", "empty.pdf")

        assert doc.pages[0].elements == []

    @patch("sayou.document.parser.pdf_parser.fitz")
    def test_scanned_page_triggers_ocr(self, mock_fitz):
        """When page text is empty and OCR engine is attached, OCR is called."""
        empty_page = MagicMock()
        empty_page.rect.width = 612.0
        empty_page.rect.height = 792.0
        empty_page.get_text.return_value = ""
        pix = MagicMock()
        pix.tobytes.return_value = b"fake_png"
        empty_page.get_pixmap.return_value = pix

        mock_fitz.open.return_value = _make_fitz_doc([empty_page])
        mock_fitz.TEXTFLAGS_DICT = 0

        mock_ocr = MagicMock()
        mock_ocr.ocr.return_value = "OCR extracted text"
        mock_ocr.component_name = "MockOCR"

        parser = PdfParser()
        parser.set_ocr_engine(mock_ocr)
        doc = parser._do_parse(b"%PDF-fake", "scanned.pdf")

        mock_ocr.ocr.assert_called_once()
        text_elems = [e for e in doc.pages[0].elements if isinstance(e, TextElement)]
        assert any(e.text == "OCR extracted text" for e in text_elems)

    @patch("sayou.document.parser.pdf_parser.fitz")
    def test_image_block_produces_image_element(self, mock_fitz):
        """Type-1 blocks (images) must produce ImageElement objects."""
        image_block = {
            "type": 1,
            "number": 1,
            "bbox": (50, 50, 200, 200),
            "image": b"\x89PNG\r\n\x1a\n" + b"\x00" * 8,
            "ext": "png",
        }
        page = _make_fitz_page(text="has image", blocks=[image_block])
        mock_fitz.open.return_value = _make_fitz_doc([page])
        mock_fitz.TEXTFLAGS_DICT = 0

        parser = PdfParser()
        doc = parser._do_parse(b"%PDF-fake", "img.pdf")

        img_elems = [e for e in doc.pages[0].elements if isinstance(e, ImageElement)]
        assert len(img_elems) == 1
        assert img_elems[0].image_base64 is not None
