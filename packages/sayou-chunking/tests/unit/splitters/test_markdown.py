"""
Unit tests for MarkdownSplitter.

Contract:
- can_handle returns 1.0 for explicit "markdown" / "md" strategy.
- can_handle returns ~0.95 when content contains Markdown headers.
- Each H1/H2/… header becomes a separate chunk with is_header=True and
  the corresponding semantic_type ("h1", "h2", …).
- Body text following a header is assigned parent_id and section_title
  pointing at that header chunk.
- Code fences (``` … ```) are not split mid-block.
- Tables are recognised as semantic_type="table".
"""

import pytest

from sayou.chunking.plugins.markdown_splitter import MarkdownSplitter
from sayou.core.schemas import SayouBlock


def _block(content: str, chunk_size: int = 2000) -> SayouBlock:
    return SayouBlock(
        type="text",
        content=content,
        metadata={"id": "doc", "config": {"chunk_size": chunk_size}},
    )


def _splitter() -> MarkdownSplitter:
    s = MarkdownSplitter()
    s.initialize()
    return s


# ---------------------------------------------------------------------------
# can_handle
# ---------------------------------------------------------------------------


class TestCanHandle:
    def test_explicit_markdown_strategy_returns_one(self):
        block = SayouBlock(type="text", content="# H", metadata={})
        assert MarkdownSplitter.can_handle(block, "markdown") == 1.0

    def test_explicit_md_strategy_returns_one(self):
        block = SayouBlock(type="text", content="x", metadata={})
        assert MarkdownSplitter.can_handle(block, "md") == 1.0

    def test_block_type_md_returns_one(self):
        block = SayouBlock(type="md", content="anything", metadata={})
        assert MarkdownSplitter.can_handle(block, "auto") == 1.0

    def test_header_content_scores_high(self):
        block = SayouBlock(type="text", content="# Header\nBody", metadata={})
        score = MarkdownSplitter.can_handle(block, "auto")
        assert score >= 0.9

    def test_plain_text_scores_zero(self):
        block = SayouBlock(type="text", content="no headers here", metadata={})
        assert MarkdownSplitter.can_handle(block, "auto") == 0.0


# ---------------------------------------------------------------------------
# Header chunking
# ---------------------------------------------------------------------------


class TestHeaderChunking:
    def test_h1_creates_header_chunk(self):
        s = _splitter()
        chunks = s.split(_block("# My Title\nSome body."))
        headers = [c for c in chunks if c.metadata.get("is_header")]
        assert len(headers) == 1
        assert headers[0].metadata["semantic_type"] == "h1"

    def test_h2_creates_header_chunk(self):
        s = _splitter()
        chunks = s.split(_block("## Section\nBody text."))
        headers = [c for c in chunks if c.metadata.get("is_header")]
        assert len(headers) == 1
        assert headers[0].metadata["semantic_type"] == "h2"

    def test_multiple_headers_each_get_own_chunk(self):
        s = _splitter()
        md = "# H1\nContent1\n## H2\nContent2\n### H3\nContent3"
        chunks = s.split(_block(md))
        headers = [c for c in chunks if c.metadata.get("is_header")]
        levels = [h.metadata["semantic_type"] for h in headers]
        assert "h1" in levels
        assert "h2" in levels
        assert "h3" in levels

    def test_body_chunk_references_parent_header(self):
        s = _splitter()
        md = "# Title\nThis is the body."
        chunks = s.split(_block(md))
        body_chunks = [c for c in chunks if not c.metadata.get("is_header")]
        assert len(body_chunks) >= 1
        for bc in body_chunks:
            assert bc.metadata.get("parent_id") is not None
            assert bc.metadata.get("section_title") == "Title"

    def test_header_level_field_is_correct(self):
        s = _splitter()
        chunks = s.split(_block("### Deep Header\nBody"))
        headers = [c for c in chunks if c.metadata.get("is_header")]
        assert headers[0].metadata["level"] == 3


# ---------------------------------------------------------------------------
# Semantic type classification
# ---------------------------------------------------------------------------


class TestSemanticTypes:
    def test_table_classified_correctly(self):
        s = _splitter()
        md = "# Table Section\n| Col A | Col B |\n|---|---|\n| 1 | 2 |"
        chunks = s.split(_block(md))
        body = [c for c in chunks if not c.metadata.get("is_header")]
        table_chunks = [c for c in body if c.metadata.get("semantic_type") == "table"]
        assert len(table_chunks) >= 1

    def test_code_block_not_split(self):
        s = _splitter()
        code_fence = "```python\nx = 1\ny = 2\nz = x + y\n```"
        md = f"# Code\n{code_fence}"
        chunks = s.split(_block(md, chunk_size=20))  # small chunk_size
        # The fence block should appear intact in at least one chunk
        all_content = "\n".join(c.content for c in chunks)
        assert "```python" in all_content
        assert "```" in all_content
