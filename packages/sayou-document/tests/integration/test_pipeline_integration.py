"""
Integration tests for DocumentPipeline.

Exercises the full parse path with real (mocked) library calls:
parser selection → parse → Document returned.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sayou.document.converter.image_converter import ImageToPdfConverter
from sayou.document.models import Document, Page, Sheet, Slide
from sayou.document.parser.excel_parser import ExcelParser
from sayou.document.parser.pdf_parser import PdfParser
from sayou.document.parser.pptx_parser import PptxParser
from sayou.document.pipeline import DocumentPipeline

# ---------------------------------------------------------------------------
# PDF end-to-end
# ---------------------------------------------------------------------------


class TestPdfIntegration:
    @patch("sayou.document.parser.pdf_parser.fitz")
    def test_pdf_bytes_route_to_pdf_parser(self, mock_fitz):
        page = MagicMock()
        page.rect.width = 612.0
        page.rect.height = 792.0
        page.get_text.return_value = "Integration test page."
        page.get_text.side_effect = lambda *a, **kw: (
            {
                "blocks": [
                    {
                        "type": 0,
                        "number": 0,
                        "bbox": (0, 0, 100, 20),
                        "lines": [{"spans": [{"text": "Integration test page."}]}],
                    }
                ]
            }
            if a and a[0] == "dict"
            else "Integration test page."
        )

        doc_mock = MagicMock()
        doc_mock.page_count = 1
        doc_mock.load_page.return_value = page
        doc_mock.get_toc.return_value = []
        mock_fitz.open.return_value = doc_mock
        mock_fitz.TEXTFLAGS_DICT = 0

        pipeline = DocumentPipeline(extra_parsers=[PdfParser])
        result = pipeline.run(b"%PDF-1.4 fake", "report.pdf")

        assert isinstance(result, Document)
        assert result.doc_type == "pdf"
        assert result.page_count == 1

    @patch("sayou.document.parser.pdf_parser.fitz")
    def test_text_content_in_page_elements(self, mock_fitz):
        page = MagicMock()
        page.rect.width = 612.0
        page.rect.height = 792.0
        page.get_text.side_effect = lambda *a, **kw: (
            {
                "blocks": [
                    {
                        "type": 0,
                        "number": 0,
                        "bbox": (0, 0, 200, 30),
                        "lines": [{"spans": [{"text": "Hello from PDF"}]}],
                    }
                ]
            }
            if a and a[0] == "dict"
            else "Hello from PDF"
        )
        doc_mock = MagicMock()
        doc_mock.page_count = 1
        doc_mock.load_page.return_value = page
        doc_mock.get_toc.return_value = []
        mock_fitz.open.return_value = doc_mock
        mock_fitz.TEXTFLAGS_DICT = 0

        pipeline = DocumentPipeline(extra_parsers=[PdfParser])
        result = pipeline.run(b"%PDF-fake", "doc.pdf")

        from sayou.document.models import TextElement

        text_elems = [e for e in result.pages[0].elements if isinstance(e, TextElement)]
        assert text_elems[0].text == "Hello from PDF"


# ---------------------------------------------------------------------------
# Excel end-to-end
# ---------------------------------------------------------------------------


class TestExcelIntegration:
    @patch("sayou.document.parser.excel_parser.openpyxl")
    def test_xlsx_bytes_route_to_excel_parser(self, mock_openpyxl):
        ws = MagicMock()
        ws.sheet_state = "visible"
        ws._images = []
        mock_row = [MagicMock(value="Header"), MagicMock(value="Value")]
        ws.iter_rows.return_value = [mock_row]

        wb = MagicMock()
        wb.sheetnames = ["Sheet1"]
        wb.__getitem__ = lambda self, k: ws
        mock_openpyxl.load_workbook.return_value = wb

        pipeline = DocumentPipeline(extra_parsers=[ExcelParser])
        result = pipeline.run(b"PK\x03\x04" + b"\x00" * 20, "data.xlsx")

        assert isinstance(result, Document)
        assert result.doc_type == "sheet"

    @patch("sayou.document.parser.excel_parser.openpyxl")
    def test_sheet_names_preserved(self, mock_openpyxl):
        def make_ws(name):
            ws = MagicMock()
            ws.sheet_state = "visible"
            ws._images = []
            ws.iter_rows.return_value = [[MagicMock(value="data")]]
            return ws

        wb = MagicMock()
        wb.sheetnames = ["Alpha", "Beta"]
        sheets = {"Alpha": make_ws("Alpha"), "Beta": make_ws("Beta")}
        wb.__getitem__ = lambda self, k: sheets[k]
        mock_openpyxl.load_workbook.return_value = wb

        pipeline = DocumentPipeline(extra_parsers=[ExcelParser])
        result = pipeline.run(b"PK\x03\x04" + b"\x00" * 20, "multi.xlsx")

        assert result.page_count == 2
        names = {p.sheet_name for p in result.pages if isinstance(p, Sheet)}
        assert names == {"Alpha", "Beta"}


# ---------------------------------------------------------------------------
# Image → PDF conversion path
# ---------------------------------------------------------------------------


class TestImageConversionIntegration:
    @patch("sayou.document.converter.image_converter.Image")
    @patch("sayou.document.parser.pdf_parser.fitz")
    def test_jpg_converts_then_parses(self, mock_fitz, mock_pil):
        # Converter: Image.open → save → return PDF bytes
        mock_img = MagicMock()
        mock_img.mode = "RGB"
        mock_pil.open.return_value = mock_img

        import io

        def fake_save(buf, format, **kw):
            buf.write(b"%PDF-converted")

        mock_img.save.side_effect = fake_save

        # Parser: fitz opens the converted PDF
        page = MagicMock()
        page.rect.width = 612.0
        page.rect.height = 792.0
        page.get_text.side_effect = lambda *a, **kw: (
            {"blocks": []} if a and a[0] == "dict" else ""
        )
        fitz_doc = MagicMock()
        fitz_doc.page_count = 1
        fitz_doc.load_page.return_value = page
        fitz_doc.get_toc.return_value = []
        mock_fitz.open.return_value = fitz_doc
        mock_fitz.TEXTFLAGS_DICT = 0

        pipeline = DocumentPipeline(
            extra_parsers=[PdfParser],
            extra_converters=[ImageToPdfConverter],
        )
        jpeg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 14

        result = pipeline.run(jpeg_bytes, "photo.jpg")
        assert isinstance(result, Document)
