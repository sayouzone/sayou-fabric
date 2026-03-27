"""
Unit tests for DocMarkdownNormalizer.

Covers:
- can_handle scoring
- page_num key fix (Bug #3 regression)
- duplicate image_base64 fix (Bug #4 regression)
- text / table / image / chart element handling
- Markdown heading/list conversion
- include_headers / include_footers flags
"""

from __future__ import annotations

import pytest
from sayou.core.schemas import SayouBlock

from sayou.refinery.normalizer.doc_markdown_normalizer import \
    DocMarkdownNormalizer

# ---------------------------------------------------------------------------
# can_handle
# ---------------------------------------------------------------------------


class TestDocMarkdownNormalizerCanHandle:
    def test_strategy_markdown_returns_1(self):
        assert DocMarkdownNormalizer.can_handle({}, "markdown") == 1.0

    def test_strategy_standard_doc_returns_1(self):
        assert DocMarkdownNormalizer.can_handle({}, "standard_doc") == 1.0

    def test_pydantic_like_object_returns_1(self):
        obj = type("Doc", (), {"doc_type": "pdf", "pages": []})()
        assert DocMarkdownNormalizer.can_handle(obj, "auto") == 1.0

    def test_markdown_string_returns_08(self):
        md = "# Title\n\nSome body text."
        score = DocMarkdownNormalizer.can_handle(md, "auto")
        assert score >= 0.8

    def test_plain_string_returns_low(self):
        score = DocMarkdownNormalizer.can_handle("plain text", "auto")
        assert score < 0.5

    def test_non_doc_returns_0(self):
        assert DocMarkdownNormalizer.can_handle(42, "auto") == 0.0


# ---------------------------------------------------------------------------
# page_num key (Bug #3 regression)
# ---------------------------------------------------------------------------


class TestPageNumKey:
    def test_page_num_extracted_correctly(self, minimal_doc_dict):
        """page_num must come from 'page_num', not the defunct 'page_index'."""
        norm = DocMarkdownNormalizer()
        norm.initialize()
        blocks = norm._do_normalize(minimal_doc_dict)

        page_nums = [b.metadata.get("page_num") for b in blocks]
        assert 1 in page_nums
        assert 2 in page_nums
        # Before the fix all blocks would have page_num=0
        assert 0 not in page_nums


# ---------------------------------------------------------------------------
# Element handling
# ---------------------------------------------------------------------------


class TestElementHandling:
    def _make_doc(self, elements):
        return {
            "file_name": "f.pdf",
            "file_id": "f",
            "doc_type": "pdf",
            "metadata": {},
            "page_count": 1,
            "pages": [
                {
                    "page_num": 1,
                    "elements": elements,
                    "header_elements": [],
                    "footer_elements": [],
                }
            ],
        }

    def test_text_element_content_preserved(self):
        doc = self._make_doc(
            [
                {
                    "type": "text",
                    "id": "t1",
                    "text": "Hello World",
                    "raw_attributes": {},
                    "meta": {"page_num": 1},
                }
            ]
        )
        norm = DocMarkdownNormalizer()
        norm.initialize()
        blocks = norm._do_normalize(doc)
        assert len(blocks) == 1
        assert "Hello World" in blocks[0].content

    def test_heading_text_gets_hashes(self):
        doc = self._make_doc(
            [
                {
                    "type": "text",
                    "id": "h1",
                    "text": "Chapter One",
                    "raw_attributes": {"semantic_type": "heading", "heading_level": 2},
                    "meta": {"page_num": 1},
                }
            ]
        )
        norm = DocMarkdownNormalizer()
        norm.initialize()
        blocks = norm._do_normalize(doc)
        assert "## Chapter One" in blocks[0].content

    def test_list_item_gets_dash(self):
        doc = self._make_doc(
            [
                {
                    "type": "text",
                    "id": "li1",
                    "text": "List item",
                    "raw_attributes": {"semantic_type": "list", "list_level": 0},
                    "meta": {"page_num": 1},
                }
            ]
        )
        norm = DocMarkdownNormalizer()
        norm.initialize()
        blocks = norm._do_normalize(doc)
        assert "- List item" in blocks[0].content

    def test_nested_list_indent(self):
        doc = self._make_doc(
            [
                {
                    "type": "text",
                    "id": "li2",
                    "text": "Nested",
                    "raw_attributes": {"semantic_type": "list", "list_level": 2},
                    "meta": {"page_num": 1},
                }
            ]
        )
        norm = DocMarkdownNormalizer()
        norm.initialize()
        blocks = norm._do_normalize(doc)
        assert "    - Nested" in blocks[0].content

    def test_table_element_becomes_markdown_table(self):
        doc = self._make_doc(
            [
                {
                    "type": "table",
                    "id": "tbl1",
                    "data": [["Name", "Score"], ["Alice", "95"]],
                    "meta": {"page_num": 1},
                }
            ]
        )
        norm = DocMarkdownNormalizer()
        norm.initialize()
        blocks = norm._do_normalize(doc)
        assert "| Name | Score |" in blocks[0].content
        assert "| --- | --- |" in blocks[0].content
        assert "| Alice | 95 |" in blocks[0].content

    def test_image_element_produces_image_base64_block(self):
        doc = self._make_doc(
            [
                {
                    "type": "image",
                    "id": "img1",
                    "image_base64": "abc123",
                    "image_format": "png",
                    "ocr_text": "Chart of results",
                    "meta": {"page_num": 1},
                }
            ]
        )
        norm = DocMarkdownNormalizer()
        norm.initialize()
        blocks = norm._do_normalize(doc)
        img_blocks = [b for b in blocks if b.type == "image_base64"]
        assert len(img_blocks) == 1
        assert img_blocks[0].content == "abc123"
        assert img_blocks[0].metadata["alt_text"] == "Chart of results"

    def test_image_without_base64_skipped(self):
        doc = self._make_doc(
            [
                {
                    "type": "image",
                    "id": "img2",
                    "image_base64": None,
                    "meta": {"page_num": 1},
                }
            ]
        )
        norm = DocMarkdownNormalizer()
        norm.initialize()
        blocks = norm._do_normalize(doc)
        img_blocks = [b for b in blocks if b.type == "image_base64"]
        assert len(img_blocks) == 0

    def test_chart_element_produces_text_block(self):
        doc = self._make_doc(
            [
                {
                    "type": "chart",
                    "id": "ch1",
                    "text_representation": "Revenue: [100, 200]",
                    "meta": {"page_num": 1},
                }
            ]
        )
        norm = DocMarkdownNormalizer()
        norm.initialize()
        blocks = norm._do_normalize(doc)
        assert any("Revenue" in b.content for b in blocks)


# ---------------------------------------------------------------------------
# Header / Footer flags
# ---------------------------------------------------------------------------


class TestHeaderFooterFlags:
    def _make_doc_with_header_footer(self):
        return {
            "file_name": "f.pdf",
            "file_id": "f",
            "doc_type": "pdf",
            "metadata": {},
            "page_count": 1,
            "pages": [
                {
                    "page_num": 1,
                    "elements": [
                        {
                            "type": "text",
                            "id": "b",
                            "text": "Body",
                            "raw_attributes": {},
                            "meta": {"page_num": 1},
                        }
                    ],
                    "header_elements": [
                        {
                            "type": "text",
                            "id": "h",
                            "text": "Header",
                            "raw_attributes": {},
                            "meta": {"page_num": 1},
                        }
                    ],
                    "footer_elements": [
                        {
                            "type": "text",
                            "id": "f",
                            "text": "Footer",
                            "raw_attributes": {},
                            "meta": {"page_num": 1},
                        }
                    ],
                }
            ],
        }

    def test_headers_included_by_default(self):
        norm = DocMarkdownNormalizer()
        norm.initialize(include_headers=True, include_footers=False)
        blocks = norm._do_normalize(self._make_doc_with_header_footer())
        combined = " ".join(b.content for b in blocks)
        assert "Header" in combined

    def test_footers_excluded_by_default(self):
        norm = DocMarkdownNormalizer()
        norm.initialize(include_headers=True, include_footers=False)
        blocks = norm._do_normalize(self._make_doc_with_header_footer())
        combined = " ".join(b.content for b in blocks)
        assert "Footer" not in combined

    def test_footers_included_when_flag_set(self):
        norm = DocMarkdownNormalizer()
        norm.initialize(include_headers=True, include_footers=True)
        blocks = norm._do_normalize(self._make_doc_with_header_footer())
        combined = " ".join(b.content for b in blocks)
        assert "Footer" in combined


# ---------------------------------------------------------------------------
# Plain string input
# ---------------------------------------------------------------------------


class TestPlainStringInput:
    def test_string_input_returns_single_md_block(self):
        norm = DocMarkdownNormalizer()
        norm.initialize()
        blocks = norm._do_normalize("# Just a Markdown string")
        assert len(blocks) == 1
        assert blocks[0].type == "md"
        assert "# Just a Markdown string" in blocks[0].content
