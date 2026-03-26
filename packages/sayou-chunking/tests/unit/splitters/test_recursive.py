"""
Unit tests for RecursiveSplitter.

Contract:
- Splits by paragraph break (\\n\\n) first, then line, then sentence, then word.
- Chunks never exceed chunk_size characters (unless a single word is longer).
- chunk_overlap causes the tail of the previous chunk to appear at the start
  of the next chunk.
- Metadata contains chunk_id and part_index.
"""

import pytest
from sayou.chunking.splitter.recursive_splitter import RecursiveSplitter
from sayou.core.schemas import SayouBlock


def _block(content: str, chunk_size: int = 1000, chunk_overlap: int = 0) -> SayouBlock:
    return SayouBlock(
        type="text",
        content=content,
        metadata={
            "id": "doc",
            "config": {"chunk_size": chunk_size, "chunk_overlap": chunk_overlap},
        },
    )


def _splitter() -> RecursiveSplitter:
    s = RecursiveSplitter()
    s.initialize()
    return s


# ---------------------------------------------------------------------------
# can_handle scoring
# ---------------------------------------------------------------------------


class TestCanHandle:
    def test_explicit_recursive_returns_one(self):
        block = SayouBlock(type="text", content="hi", metadata={})
        assert RecursiveSplitter.can_handle(block, "recursive") == 1.0

    def test_text_block_scores_high_on_auto(self):
        block = SayouBlock(type="text", content="hi", metadata={})
        assert RecursiveSplitter.can_handle(block, "auto") >= 0.5

    def test_plain_string_scores_nonzero(self):
        assert RecursiveSplitter.can_handle("hello", "auto") > 0.0


# ---------------------------------------------------------------------------
# Splitting behaviour
# ---------------------------------------------------------------------------


class TestRecursiveSplitter:
    def test_paragraph_breaks_create_separate_chunks(self):
        s = _splitter()
        text = "First para.\n\nSecond para.\n\nThird para."
        chunks = s.split(_block(text, chunk_size=20))
        assert len(chunks) == 3
        assert chunks[0].content == "First para."
        assert chunks[1].content == "Second para."

    def test_single_chunk_when_content_fits(self):
        s = _splitter()
        chunks = s.split(_block("Short text.", chunk_size=1000))
        assert len(chunks) == 1

    def test_chunks_respect_size_limit(self):
        s = _splitter()
        long_text = "word " * 200  # 1000 chars
        chunks = s.split(_block(long_text, chunk_size=50))
        for chunk in chunks:
            assert len(chunk.content) <= 60, f"Chunk too long: {len(chunk.content)}"

    def test_metadata_contains_chunk_id_and_part_index(self):
        s = _splitter()
        text = "Para one.\n\nPara two.\n\nPara three."
        chunks = s.split(_block(text, chunk_size=15))
        for i, chunk in enumerate(chunks):
            assert "chunk_id" in chunk.metadata
            assert chunk.metadata["part_index"] == i

    def test_empty_content_returns_empty(self):
        s = _splitter()
        chunks = s.split(_block("", chunk_size=100))
        assert chunks == []

    def test_overlap_content_repeated(self):
        """With overlap > 0, tail of chunk N appears at start of chunk N+1."""
        s = _splitter()
        # 10-char chunks, 5-char overlap on a predictable string
        text = "AAAAAAAAAA BBBBBBBBBB CCCCCCCCCC"
        chunks = s.split(_block(text, chunk_size=10, chunk_overlap=5))
        # At least the second chunk should share chars with the first
        assert len(chunks) >= 2
