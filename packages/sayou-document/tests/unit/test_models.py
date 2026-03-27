"""
Unit tests for sayou-document models.

Covers:
- Field presence and default values
- TextElement.text field (Bug #1 regression guard)
- Slide.text field (Bug #2 regression guard)
- BoundingBox, TextStyle, ElementMetadata
- TableElement.text property
- ImageElement.text property
- ChartElement.text property
- Document structure
"""

from __future__ import annotations

import pytest

from sayou.document.models import (
    BoundingBox,
    ChartElement,
    Document,
    DocumentMetadata,
    ElementMetadata,
    ImageElement,
    Page,
    Sheet,
    Slide,
    TableCell,
    TableElement,
    TextElement,
    TextStyle,
)


# ---------------------------------------------------------------------------
# BoundingBox
# ---------------------------------------------------------------------------


class TestBoundingBox:
    def test_defaults(self):
        bb = BoundingBox()
        assert bb.x0 == 0.0
        assert bb.y0 == 0.0
        assert bb.x1 == 0.0
        assert bb.y1 == 0.0

    def test_explicit_values(self):
        bb = BoundingBox(x0=10, y0=20, x1=100, y1=200)
        assert bb.x0 == 10.0
        assert bb.y1 == 200.0


# ---------------------------------------------------------------------------
# ElementMetadata
# ---------------------------------------------------------------------------


class TestElementMetadata:
    def test_required_page_num(self):
        meta = ElementMetadata(page_num=3)
        assert meta.page_num == 3
        assert meta.id is None
        assert meta.link is None

    def test_extra_fields_allowed(self):
        meta = ElementMetadata(page_num=1, custom_key="hello")
        assert meta.custom_key == "hello"


# ---------------------------------------------------------------------------
# TextElement — Bug #1 regression
# ---------------------------------------------------------------------------


class TestTextElement:
    def test_text_field_is_not_commented_out(self):
        """Regression: text field was accidentally commented out."""
        elem = TextElement(
            id="t1",
            text="Hello World",
            meta=ElementMetadata(page_num=1),
        )
        # The field must survive the round-trip — not be swallowed by the
        # BaseElement.text property returning ""
        assert elem.text == "Hello World"

    def test_text_default_empty_string(self):
        elem = TextElement(id="t2", meta=ElementMetadata(page_num=1))
        assert elem.text == ""

    def test_text_persists_after_model_dump(self):
        elem = TextElement(id="t3", text="Persist me", meta=ElementMetadata(page_num=1))
        dumped = elem.model_dump()
        assert dumped["text"] == "Persist me"

    def test_type_literal(self):
        elem = TextElement(id="t4", meta=ElementMetadata(page_num=1))
        assert elem.type == "text"

    def test_style_optional(self):
        style = TextStyle(font_name="Arial", font_size=12.0, is_bold=True)
        elem = TextElement(
            id="t5", text="Styled", meta=ElementMetadata(page_num=1), style=style
        )
        assert elem.style.is_bold is True


# ---------------------------------------------------------------------------
# TableElement
# ---------------------------------------------------------------------------


class TestTableElement:
    def make(self) -> TableElement:
        return TableElement(
            id="tbl1",
            data=[["Name", "Score"], ["Alice", "95"], ["Bob", "80"]],
            meta=ElementMetadata(page_num=1),
        )

    def test_text_property_produces_tsv(self):
        tbl = self.make()
        lines = tbl.text.split("\n")
        assert lines[0] == "Name\tScore"
        assert lines[1] == "Alice\t95"

    def test_empty_data_returns_empty_string(self):
        tbl = TableElement(id="tbl2", data=[], meta=ElementMetadata(page_num=1))
        assert tbl.text == ""

    def test_cells_optional(self):
        tbl = self.make()
        assert tbl.cells == []

    def test_caption_optional(self):
        tbl = self.make()
        assert tbl.caption is None


# ---------------------------------------------------------------------------
# ImageElement
# ---------------------------------------------------------------------------


class TestImageElement:
    def test_text_returns_ocr_text_when_present(self):
        img = ImageElement(
            id="img1",
            ocr_text="Extracted OCR text",
            meta=ElementMetadata(page_num=1),
        )
        assert img.text == "Extracted OCR text"

    def test_text_falls_back_to_caption(self):
        img = ImageElement(
            id="img2",
            caption="Figure 1",
            meta=ElementMetadata(page_num=1),
        )
        assert img.text == "Figure 1"

    def test_text_empty_when_no_ocr_or_caption(self):
        img = ImageElement(id="img3", meta=ElementMetadata(page_num=1))
        assert img.text == ""


# ---------------------------------------------------------------------------
# ChartElement
# ---------------------------------------------------------------------------


class TestChartElement:
    def test_text_returns_text_representation(self):
        chart = ChartElement(
            id="ch1",
            text_representation="Revenue: 100, 200, 300",
            meta=ElementMetadata(page_num=2),
        )
        assert chart.text == "Revenue: 100, 200, 300"

    def test_text_falls_back_to_title(self):
        chart = ChartElement(
            id="ch2",
            chart_title="Q1 Sales",
            meta=ElementMetadata(page_num=2),
        )
        assert chart.text == "Q1 Sales"

    def test_text_empty_when_no_data(self):
        chart = ChartElement(id="ch3", meta=ElementMetadata(page_num=2))
        assert chart.text == ""


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------


class TestPage:
    def test_page_fields(self):
        page = Page(page_num=1, width=612.0, height=792.0)
        assert page.page_num == 1
        assert page.elements == []
        assert page.header_elements == []
        assert page.footer_elements == []
        assert page.text is None

    def test_page_with_elements(self):
        elem = TextElement(id="t1", text="body text", meta=ElementMetadata(page_num=1))
        page = Page(page_num=1, elements=[elem], text="body text")
        assert len(page.elements) == 1
        assert page.text == "body text"


# ---------------------------------------------------------------------------
# Slide — Bug #2 regression
# ---------------------------------------------------------------------------


class TestSlide:
    def test_text_field_exists(self):
        """Regression: Slide lacked a text field; PptxParser silently dropped it."""
        slide = Slide(page_num=1, text="Slide text content")
        assert slide.text == "Slide text content"

    def test_text_field_default_none(self):
        slide = Slide(page_num=1)
        assert slide.text is None

    def test_note_text_and_has_notes(self):
        slide = Slide(page_num=1, note_text="Speaker notes here", has_notes=True)
        assert slide.has_notes is True
        assert slide.note_text == "Speaker notes here"


# ---------------------------------------------------------------------------
# Sheet
# ---------------------------------------------------------------------------


class TestSheet:
    def test_sheet_fields(self):
        sheet = Sheet(page_num=1, sheet_name="Data", sheet_index=0)
        assert sheet.sheet_name == "Data"
        assert sheet.is_hidden is False
        assert sheet.sheet_index == 0


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------


class TestDocument:
    def test_minimal_document(self):
        doc = Document(
            file_name="report.pdf",
            file_id="report.pdf",
            doc_type="pdf",
        )
        assert doc.page_count == 0
        assert doc.pages == []
        assert doc.toc == []
        assert doc.links == []

    def test_document_with_pages(self):
        page = Page(page_num=1)
        doc = Document(
            file_name="doc.pdf",
            file_id="doc.pdf",
            doc_type="pdf",
            page_count=1,
            pages=[page],
        )
        assert len(doc.pages) == 1

    def test_metadata_defaults(self):
        doc = Document(file_name="f.pdf", file_id="f.pdf", doc_type="pdf")
        assert doc.metadata.title is None
        assert doc.metadata.author is None
        assert doc.metadata.extra == {}

    def test_doc_types(self):
        for doc_type in ["pdf", "word", "slide", "sheet", "unknown"]:
            doc = Document(file_name="f", file_id="f", doc_type=doc_type)
            assert doc.doc_type == doc_type
