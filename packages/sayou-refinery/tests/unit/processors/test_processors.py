"""
Unit tests for all Refinery processors:
- TextCleaner
- PiiMasker
- Deduplicator
- Imputer
- OutlierHandler
- RecursivePruner
- LinkProcessor
- WhiteSpaceProcessor
"""

from __future__ import annotations

import pytest
from sayou.core.schemas import SayouBlock

from sayou.refinery.processor.text_cleaner import TextCleaner
from sayou.refinery.processor.pii_masker import PiiMasker
from sayou.refinery.processor.deduplicator import Deduplicator
from sayou.refinery.processor.imputer import Imputer
from sayou.refinery.processor.outlier_handler import OutlierHandler
from sayou.refinery.processor.recursive_pruner import RecursivePruner
from sayou.refinery.plugins.link_processor import LinkProcessor
from sayou.refinery.plugins.white_space_processor import WhiteSpaceProcessor


def _text(content: str, **meta) -> SayouBlock:
    return SayouBlock(type="text", content=content, metadata=meta)


def _md(content: str, **meta) -> SayouBlock:
    return SayouBlock(type="md", content=content, metadata=meta)


def _record(content: dict, **meta) -> SayouBlock:
    return SayouBlock(type="record", content=content, metadata=meta)


# ===========================================================================
# TextCleaner
# ===========================================================================


class TestTextCleaner:
    def test_removes_custom_pattern(self):
        cleaner = TextCleaner()
        cleaner.initialize(patterns=[r"\[AD\]"])
        blocks = cleaner._do_process([_text("Hello [AD] World")])
        assert "[AD]" not in blocks[0].content
        assert "Hello" in blocks[0].content

    def test_normalizes_whitespace(self):
        cleaner = TextCleaner()
        cleaner.initialize(normalize_space=True)
        blocks = cleaner._do_process([_text("too   many    spaces")])
        assert "  " not in blocks[0].content

    def test_skips_non_text_blocks(self):
        cleaner = TextCleaner()
        cleaner.initialize()
        rec = _record({"key": "value"})
        result = cleaner._do_process([rec])
        assert result[0].content == {"key": "value"}

    def test_multiple_patterns(self):
        cleaner = TextCleaner()
        cleaner.initialize(patterns=[r"\[AD\]", r"\[PROMO\]"])
        blocks = cleaner._do_process([_text("[AD] Buy now [PROMO] today")])
        assert "[AD]" not in blocks[0].content
        assert "[PROMO]" not in blocks[0].content

    def test_md_block_also_cleaned(self):
        cleaner = TextCleaner()
        cleaner.initialize(patterns=[r"NOISE"])
        blocks = cleaner._do_process([_md("# Title\n\nNOISE content")])
        assert "NOISE" not in blocks[0].content


# ===========================================================================
# PiiMasker
# ===========================================================================


class TestPiiMasker:
    def test_masks_email(self):
        masker = PiiMasker()
        masker.initialize(mask_email=True, mask_phone=False)
        blocks = masker._do_process([_text("Contact alice@example.com for info.")])
        assert "[EMAIL]" in blocks[0].content
        assert "alice@example.com" not in blocks[0].content

    def test_masks_phone(self):
        masker = PiiMasker()
        masker.initialize(mask_email=False, mask_phone=True)
        blocks = masker._do_process([_text("Call 010-1234-5678 now.")])
        assert "[PHONE]" in blocks[0].content
        assert "010-1234-5678" not in blocks[0].content

    def test_both_masked_simultaneously(self):
        masker = PiiMasker()
        masker.initialize()
        blocks = masker._do_process([_text("Email bob@test.com or call 010-9876-5432")])
        assert "[EMAIL]" in blocks[0].content
        assert "[PHONE]" in blocks[0].content

    def test_skips_non_text_blocks(self):
        masker = PiiMasker()
        masker.initialize()
        rec = _record({"email": "alice@example.com"})
        result = masker._do_process([rec])
        # record blocks are untouched
        assert result[0].content["email"] == "alice@example.com"

    def test_email_masking_disabled(self):
        masker = PiiMasker()
        masker.initialize(mask_email=False, mask_phone=False)
        blocks = masker._do_process([_text("user@domain.com stays")])
        assert "user@domain.com" in blocks[0].content


# ===========================================================================
# Deduplicator
# ===========================================================================


class TestDeduplicator:
    def test_removes_duplicate_text_blocks(self):
        dedup = Deduplicator()
        blocks = [_text("same content"), _text("same content"), _text("different")]
        result = dedup._do_process(blocks)
        assert len(result) == 2

    def test_keeps_unique_blocks(self):
        dedup = Deduplicator()
        blocks = [_text("a"), _text("b"), _text("c")]
        result = dedup._do_process(blocks)
        assert len(result) == 3

    def test_duplicate_records_removed(self):
        dedup = Deduplicator()
        data = {"id": "1", "name": "Alice"}
        blocks = [_record(data), _record(data)]
        result = dedup._do_process(blocks)
        assert len(result) == 1

    def test_very_short_content_not_deduplicated(self):
        """Blocks with content < 5 chars bypass dedup (by design)."""
        dedup = Deduplicator()
        blocks = [_text("ok"), _text("ok")]
        result = dedup._do_process(blocks)
        assert len(result) == 2

    def test_empty_list_returns_empty(self):
        dedup = Deduplicator()
        assert dedup._do_process([]) == []


# ===========================================================================
# Imputer
# ===========================================================================


class TestImputer:
    def test_fills_missing_fields(self):
        imputer = Imputer()
        imputer.initialize(imputation_rules={"category": "Unknown", "score": 0.0})
        block = _record({"id": "1", "name": "Alice"})
        result = imputer._do_process([block])
        assert result[0].content["category"] == "Unknown"
        assert result[0].content["score"] == 0.0

    def test_does_not_overwrite_existing(self):
        imputer = Imputer()
        imputer.initialize(imputation_rules={"score": 0.0})
        block = _record({"id": "1", "score": 95})
        result = imputer._do_process([block])
        assert result[0].content["score"] == 95

    def test_skips_non_record_blocks(self):
        imputer = Imputer()
        imputer.initialize(imputation_rules={"x": 1})
        block = _text("plain text")
        result = imputer._do_process([block])
        assert result[0].content == "plain text"

    def test_no_rules_is_safe(self):
        imputer = Imputer()
        imputer.initialize()
        block = _record({"a": None})
        result = imputer._do_process([block])
        assert result[0].content["a"] is None


# ===========================================================================
# OutlierHandler
# ===========================================================================


class TestOutlierHandler:
    def test_drop_action_removes_violating_block(self):
        handler = OutlierHandler()
        handler.initialize(
            outlier_rules={"age": {"min": 0, "max": 120, "action": "drop"}}
        )
        blocks = [
            _record({"age": 25}),
            _record({"age": -5}),  # violates min
            _record({"age": 200}),  # violates max
        ]
        result = handler._do_process(blocks)
        assert len(result) == 1
        assert result[0].content["age"] == 25

    def test_clamp_action_clips_value(self):
        handler = OutlierHandler()
        handler.initialize(
            outlier_rules={"score": {"min": 0, "max": 100, "action": "clamp"}}
        )
        blocks = [
            _record({"score": 150}),
            _record({"score": -10}),
        ]
        result = handler._do_process(blocks)
        assert result[0].content["score"] == 100
        assert result[1].content["score"] == 0

    def test_non_record_blocks_pass_through(self):
        handler = OutlierHandler()
        handler.initialize(outlier_rules={"x": {"min": 0, "max": 10, "action": "drop"}})
        block = _text("plain text")
        result = handler._do_process([block])
        assert len(result) == 1

    def test_non_numeric_values_ignored(self):
        handler = OutlierHandler()
        handler.initialize(
            outlier_rules={"name": {"min": 0, "max": 10, "action": "drop"}}
        )
        block = _record({"name": "Alice"})
        result = handler._do_process([block])
        assert len(result) == 1

    def test_missing_field_skipped(self):
        handler = OutlierHandler()
        handler.initialize(
            outlier_rules={"age": {"min": 0, "max": 120, "action": "drop"}}
        )
        block = _record({"name": "No age field"})
        result = handler._do_process([block])
        assert len(result) == 1


# ===========================================================================
# RecursivePruner
# ===========================================================================


class TestRecursivePruner:
    def test_removes_none_values(self):
        pruner = RecursivePruner()
        block = _record({"a": "value", "b": None, "c": ""})
        result = pruner._do_process([block])
        assert "b" not in result[0].content
        assert "c" not in result[0].content
        assert result[0].content["a"] == "value"

    def test_removes_empty_nested_dict(self):
        pruner = RecursivePruner()
        block = _record({"a": {"b": None, "c": None}})
        result = pruner._do_process([block])
        # inner dict becomes {} → pruned → outer dict becomes {} → block removed
        assert len(result) == 0

    def test_removes_null_string(self):
        pruner = RecursivePruner()
        block = _record({"status": "NULL", "name": "Alice"})
        result = pruner._do_process([block])
        assert "status" not in result[0].content
        assert result[0].content["name"] == "Alice"

    def test_empty_list_pruned(self):
        pruner = RecursivePruner()
        block = _record({"tags": [], "name": "Bob"})
        result = pruner._do_process([block])
        assert "tags" not in result[0].content

    def test_block_with_all_empty_removed(self):
        pruner = RecursivePruner()
        block = _record({"a": None, "b": "", "c": []})
        result = pruner._do_process([block])
        assert len(result) == 0


# ===========================================================================
# LinkProcessor
# ===========================================================================


class TestLinkProcessor:
    def _run(self, content: str, remove_links: bool = False) -> SayouBlock:
        proc = LinkProcessor()
        proc.initialize(remove_links=remove_links)
        blocks = proc._do_process([_text(content)])
        return blocks[0]

    def test_raw_url_extracted_to_metadata(self):
        block = self._run("Visit https://example.com for more.")
        assert any(
            l["url"] == "https://example.com" for l in block.metadata.get("links", [])
        )

    def test_markdown_link_extracted(self):
        block = self._run("See [Sayou](https://sayouzone.com) here.")
        links = block.metadata.get("links", [])
        assert any(l["title"] == "Sayou" and "sayouzone" in l["url"] for l in links)

    def test_remove_links_strips_url(self):
        block = self._run("Check https://example.com today.", remove_links=True)
        assert "https://example.com" not in block.content

    def test_remove_links_keeps_markdown_text(self):
        block = self._run("[Click here](https://example.com)", remove_links=True)
        assert "Click here" in block.content
        assert "https://example.com" not in block.content

    def test_non_text_blocks_skipped(self):
        proc = LinkProcessor()
        proc.initialize()
        rec = _record({"url": "https://example.com"})
        result = proc._do_process([rec])
        assert "links" not in result[0].metadata


# ===========================================================================
# WhiteSpaceProcessor
# ===========================================================================


class TestWhiteSpaceProcessor:
    def test_collapses_multiple_spaces(self):
        proc = WhiteSpaceProcessor()
        proc.initialize(preserve_newlines=True)
        blocks = proc._do_process([_text("too   many   spaces")])
        assert "  " not in blocks[0].content

    def test_replaces_nbsp(self):
        proc = WhiteSpaceProcessor()
        proc.initialize()
        blocks = proc._do_process([_text("non\xa0breaking\xa0space")])
        assert "\xa0" not in blocks[0].content

    def test_preserve_newlines_true_keeps_paragraphs(self):
        proc = WhiteSpaceProcessor()
        proc.initialize(preserve_newlines=True)
        blocks = proc._do_process([_text("Para one.\n\nPara two.")])
        assert "\n\n" in blocks[0].content

    def test_preserve_newlines_false_flattens(self):
        proc = WhiteSpaceProcessor()
        proc.initialize(preserve_newlines=False)
        blocks = proc._do_process([_text("Line one.\n\nLine two.")])
        assert "\n" not in blocks[0].content

    def test_record_string_fields_cleaned(self):
        proc = WhiteSpaceProcessor()
        proc.initialize()
        rec = _record({"name": "  Alice  ", "bio": "too   many   spaces"})
        result = proc._do_process([rec])
        assert result[0].content["name"].strip() == "Alice"
        assert "  " not in result[0].content["bio"]

    def test_removes_zero_width_space(self):
        proc = WhiteSpaceProcessor()
        proc.initialize()
        blocks = proc._do_process([_text("invis\u200bible")])
        assert "\u200b" not in blocks[0].content
