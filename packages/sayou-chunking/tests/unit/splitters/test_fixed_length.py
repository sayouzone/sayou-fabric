"""
Unit tests for FixedLengthSplitter and AuditedFixedLengthSplitter.

FixedLengthSplitter contract:
- Slices content into equal-sized windows of exactly `chunk_size` characters.
- The last window may be shorter than `chunk_size`.
- `chunk_overlap` shifts the window start left by N characters (step = size - overlap).
- Raises ValueError when chunk_overlap >= chunk_size.

AuditedFixedLengthSplitter adds audit metadata (processed_at, original_length,
splitter_version) to every chunk produced by the parent class.
"""

import pytest

from sayou.chunking.splitter.fixed_length_splitter import FixedLengthSplitter
from sayou.chunking.plugins.audited_fixed_length_splitter import (
    AuditedFixedLengthSplitter,
)
from sayou.core.schemas import SayouBlock


def _block(content: str, chunk_size: int, chunk_overlap: int = 0) -> SayouBlock:
    return SayouBlock(
        type="text",
        content=content,
        metadata={"config": {"chunk_size": chunk_size, "chunk_overlap": chunk_overlap}},
    )


def _splitter() -> FixedLengthSplitter:
    s = FixedLengthSplitter()
    s.initialize()
    return s


# ---------------------------------------------------------------------------
# can_handle
# ---------------------------------------------------------------------------


class TestCanHandle:
    def test_explicit_strategy_returns_one(self):
        assert (
            FixedLengthSplitter.can_handle(
                SayouBlock(type="text", content="x", metadata={}), "fixed_length"
            )
            == 1.0
        )

    def test_auto_strategy_returns_nonzero_for_string_input(self):
        """FixedLengthSplitter scores plain strings > 0, but not SayouBlock."""
        assert FixedLengthSplitter.can_handle("hello world", "auto") > 0.0

    def test_auto_strategy_returns_zero_for_sayou_block(self):
        """FixedLengthSplitter does not self-select for generic text blocks."""
        block = SayouBlock(type="text", content="hello", metadata={})
        assert FixedLengthSplitter.can_handle(block, "auto") == 0.0

    def test_unrelated_strategy_returns_zero(self):
        block = SayouBlock(type="text", content="x", metadata={})
        assert FixedLengthSplitter.can_handle(block, "markdown") == 0.0


# ---------------------------------------------------------------------------
# Core splitting behaviour
# ---------------------------------------------------------------------------


class TestFixedLengthSplitter:
    def test_exact_split_no_overlap(self):
        s = _splitter()
        chunks = s.split(_block("1234567890", chunk_size=5, chunk_overlap=0))
        assert len(chunks) == 2
        assert chunks[0].content == "12345"
        assert chunks[1].content == "67890"

    def test_last_chunk_shorter_than_size(self):
        s = _splitter()
        chunks = s.split(_block("ABCDE", chunk_size=3, chunk_overlap=0))
        assert len(chunks) == 2
        assert chunks[0].content == "ABC"
        assert chunks[1].content == "DE"

    def test_content_shorter_than_chunk_size_yields_one_chunk(self):
        s = _splitter()
        chunks = s.split(_block("Hi", chunk_size=100))
        assert len(chunks) == 1
        assert chunks[0].content == "Hi"

    def test_overlap_shifts_window(self):
        s = _splitter()
        # size=5, overlap=2 → step=3: windows start at 0, 3, 6
        chunks = s.split(_block("0123456789", chunk_size=5, chunk_overlap=2))
        assert chunks[0].content == "01234"
        assert chunks[1].content == "34567"
        assert chunks[2].content == "6789"

    def test_invalid_overlap_raises_splitter_error(self):
        from sayou.chunking.core.exceptions import SplitterError

        s = _splitter()
        with pytest.raises(SplitterError, match="chunk_overlap"):
            s.split(_block("hello", chunk_size=3, chunk_overlap=3))

    def test_single_character_chunks(self):
        s = _splitter()
        chunks = s.split(_block("ABC", chunk_size=1, chunk_overlap=0))
        assert len(chunks) == 3
        assert [c.content for c in chunks] == ["A", "B", "C"]


# ---------------------------------------------------------------------------
# AuditedFixedLengthSplitter — audit metadata
# ---------------------------------------------------------------------------


class TestAuditedFixedLengthSplitter:
    def _splitter(self) -> AuditedFixedLengthSplitter:
        s = AuditedFixedLengthSplitter()
        s.initialize()
        return s

    def test_audit_keys_present_on_every_chunk(self):
        s = self._splitter()
        chunks = s.split(_block("ABCDEFGH", chunk_size=4))
        for chunk in chunks:
            audit = chunk.metadata.get("audit")
            assert audit is not None, "audit key missing"
            assert "processed_at" in audit
            assert "original_length" in audit
            assert "splitter_version" in audit

    def test_original_length_is_correct(self):
        s = self._splitter()
        content = "Hello World"
        chunks = s.split(_block(content, chunk_size=5))
        for chunk in chunks:
            assert chunk.metadata["audit"]["original_length"] == len(content)

    def test_audited_strategy_returns_one_from_can_handle(self):
        block = SayouBlock(type="text", content="x", metadata={})
        assert AuditedFixedLengthSplitter.can_handle(block, "audited_fixed") == 1.0
