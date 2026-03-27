"""
Integration tests for RefineryPipeline.

Exercises the full normalize → process chain using real plugin instances.
"""

from __future__ import annotations

import pytest
from sayou.core.schemas import SayouBlock

from sayou.refinery.normalizer.doc_markdown_normalizer import \
    DocMarkdownNormalizer
from sayou.refinery.normalizer.html_text_normalizer import HtmlTextNormalizer
from sayou.refinery.normalizer.raw_json_normalizer import RawJsonNormalizer
from sayou.refinery.normalizer.record_normalizer import RecordNormalizer
from sayou.refinery.pipeline import RefineryPipeline
from sayou.refinery.plugins.white_space_processor import WhiteSpaceProcessor
from sayou.refinery.processor.deduplicator import Deduplicator
from sayou.refinery.processor.pii_masker import PiiMasker
from sayou.refinery.processor.recursive_pruner import RecursivePruner
from sayou.refinery.processor.text_cleaner import TextCleaner

# ---------------------------------------------------------------------------
# DocMarkdownNormalizer → TextCleaner
# ---------------------------------------------------------------------------


class TestDocMarkdownWithProcessors:
    def test_markdown_string_cleaned(self):
        pipeline = RefineryPipeline(
            extra_normalizers=[DocMarkdownNormalizer],
            extra_processors=[TextCleaner],
        )
        raw = "# Title\n\n[AD] Some   noisy   text."
        blocks = pipeline.run(
            raw,
            strategy="markdown",
            processors=["TextCleaner"],
            patterns=["\\[AD\\]"],
        )
        assert len(blocks) >= 1
        assert "[AD]" not in blocks[0].content

    def test_doc_dict_normalised_to_md_blocks(self, minimal_doc_dict):
        pipeline = RefineryPipeline(
            extra_normalizers=[DocMarkdownNormalizer],
        )
        blocks = pipeline.run(minimal_doc_dict, strategy="markdown")
        assert len(blocks) >= 1
        assert all(b.type in ("md", "image_base64") for b in blocks)

    def test_heading_element_gets_hashes(self, minimal_doc_dict):
        pipeline = RefineryPipeline(
            extra_normalizers=[DocMarkdownNormalizer],
        )
        blocks = pipeline.run(minimal_doc_dict, strategy="markdown")
        combined = " ".join(b.content for b in blocks if b.type == "md")
        assert "## Conclusion" in combined


# ---------------------------------------------------------------------------
# HtmlTextNormalizer → PiiMasker
# ---------------------------------------------------------------------------


class TestHtmlWithPiiMasker:
    def test_html_pii_masked(self):
        try:
            from bs4 import BeautifulSoup  # noqa: F401
        except ImportError:
            pytest.skip("beautifulsoup4 not installed")

        pipeline = RefineryPipeline(
            extra_normalizers=[HtmlTextNormalizer],
            extra_processors=[PiiMasker],
        )
        html = "<html><body><p>Email alice@example.com or call 010-1234-5678</p></body></html>"
        blocks = pipeline.run(html, strategy="html", processors=["PiiMasker"])
        combined = " ".join(b.content for b in blocks)
        assert "[EMAIL]" in combined
        assert "[PHONE]" in combined


# ---------------------------------------------------------------------------
# RecordNormalizer → RecursivePruner → Deduplicator
# ---------------------------------------------------------------------------


class TestRecordPipeline:
    def test_null_fields_pruned_then_deduplicated(self):
        pipeline = RefineryPipeline(
            extra_normalizers=[RecordNormalizer],
            extra_processors=[RecursivePruner, Deduplicator],
        )
        data = [
            {"id": "1", "name": "Alice", "email": None},
            {"id": "2", "name": "Bob", "bio": ""},
            {"id": "1", "name": "Alice", "email": None},  # duplicate
        ]
        blocks = pipeline.run(
            data,
            strategy="record",
            processors=["RecursivePruner", "Deduplicator"],
        )
        # Null fields pruned
        for b in blocks:
            if isinstance(b.content, dict):
                assert "email" not in b.content or b.content.get("email") is not None
        # Dedup: original 3 → after pruning duplicates become identical → 2 unique
        assert len(blocks) <= 2

    def test_record_with_content_meta_separation(self):
        pipeline = RefineryPipeline(
            extra_normalizers=[RecordNormalizer],
        )
        data = {
            "content": [{"text": "Hello.", "start": 0.0}],
            "meta": {"source": "youtube", "video_id": "abc"},
        }
        blocks = pipeline.run(data, strategy="record")
        assert len(blocks) == 1
        assert blocks[0].metadata.get("video_id") == "abc"


# ---------------------------------------------------------------------------
# RawJsonNormalizer → WhiteSpaceProcessor
# ---------------------------------------------------------------------------


class TestRawJsonPipeline:
    def test_whitespace_cleaned_in_record_fields(self):
        pipeline = RefineryPipeline(
            extra_normalizers=[RawJsonNormalizer],
            extra_processors=[WhiteSpaceProcessor],
        )
        data = {"id": "1", "bio": "too   many   spaces\xa0here"}
        blocks = pipeline.run(
            data,
            strategy="raw_json",
            processors=["WhiteSpaceProcessor"],
        )
        assert len(blocks) == 1
        bio = blocks[0].content.get("bio", "")
        assert "  " not in bio
        assert "\xa0" not in bio


# ---------------------------------------------------------------------------
# Empty and edge inputs
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_none_input_returns_empty(self):
        pipeline = RefineryPipeline(extra_normalizers=[DocMarkdownNormalizer])
        result = pipeline.run(None)
        assert result == []

    def test_empty_string_returns_block(self):
        pipeline = RefineryPipeline(extra_normalizers=[DocMarkdownNormalizer])
        blocks = pipeline.run("", strategy="markdown")
        # Empty string normalizes to one empty md block or empty list
        assert isinstance(blocks, list)

    def test_process_facade_runs_full_chain(self, minimal_doc_dict):
        blocks = RefineryPipeline.process(
            minimal_doc_dict,
            strategy="markdown",
            extra_normalizers=[DocMarkdownNormalizer],
        )
        assert isinstance(blocks, list)
