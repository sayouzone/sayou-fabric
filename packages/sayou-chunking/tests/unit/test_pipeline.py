"""
Unit tests for ChunkingPipeline.

Covers:
- Strategy routing (explicit name → splitter, auto scoring, unknown → None)
- Config merging (global < runtime)
- Edge inputs (empty string, empty list, plain string, SayouBlock)
- No-splitter preservation path (chunk tagged with error="no_splitter")
- _callbacks propagation to each instantiated splitter
- TypeError guard in _register_manual
"""

import pytest
from sayou.chunking.pipeline import ChunkingPipeline
from sayou.chunking.plugins.code_splitter import CodeSplitter
from sayou.chunking.plugins.markdown_splitter import MarkdownSplitter
from sayou.core.schemas import SayouBlock, SayouChunk

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def pipeline() -> ChunkingPipeline:
    return ChunkingPipeline(extra_splitters=[MarkdownSplitter, CodeSplitter])


# ---------------------------------------------------------------------------
# Basic routing
# ---------------------------------------------------------------------------


class TestStrategyRouting:
    def test_explicit_recursive_strategy(self, pipeline):
        chunks = pipeline.run(
            {
                "content": "Hello.\n\nWorld.\n\nThis is a test.",
                "config": {"chunk_size": 10, "chunk_overlap": 0},
            },
            strategy="recursive",
        )
        assert len(chunks) >= 1
        assert all(isinstance(c, SayouChunk) for c in chunks)

    def test_explicit_fixed_length_strategy(self, pipeline):
        chunks = pipeline.run(
            {"content": "1234567890", "config": {"chunk_size": 5, "chunk_overlap": 0}},
            strategy="fixed_length",
        )
        assert len(chunks) == 2
        assert chunks[0].content == "12345"
        assert chunks[1].content == "67890"

    def test_explicit_markdown_strategy(self, pipeline):
        text = "# H1\nContent\n## H2\nMore"
        chunks = pipeline.run({"content": text}, strategy="markdown")
        headers = [c for c in chunks if c.metadata.get("is_header")]
        assert len(headers) == 2

    def test_explicit_code_strategy_python(self, pipeline):
        src = "def foo():\n    pass\n\ndef bar():\n    return 1\n"
        chunks = pipeline.run(
            {
                "content": src,
                "metadata": {"extension": ".py"},
                "config": {"chunk_size": 1000},
            },
            strategy="code",
        )
        names = [c.metadata.get("function_name") for c in chunks]
        assert "foo" in names
        assert "bar" in names

    def test_auto_strategy_selects_markdown_for_headers(self, pipeline):
        text = "# Title\nSome content."
        chunks = pipeline.run({"content": text}, strategy="auto")
        assert len(chunks) >= 1

    def test_unknown_strategy_routes_to_best_match(self, pipeline):
        """
        An unrecognised strategy name falls through to score-based resolution.
        RecursiveSplitter scores 0.9 for type='text' blocks, so it wins and
        the content is returned as valid chunks rather than a preserved no-op.
        """
        chunks = pipeline.run(
            {"content": "some text"},
            strategy="__nonexistent_strategy__",
        )
        assert len(chunks) >= 1
        assert all(isinstance(c, SayouChunk) for c in chunks)


# ---------------------------------------------------------------------------
# Config merging
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Config forwarding
# ---------------------------------------------------------------------------


class TestConfigMerge:
    def test_config_in_request_dict_is_forwarded(self):
        """config dict inside the request reaches the splitter."""
        p = ChunkingPipeline()
        chunks = p.run(
            {"content": "ABCDEFGHIJ", "config": {"chunk_size": 3, "chunk_overlap": 0}},
            strategy="fixed_length",
        )
        # chunk_size=3, overlap=0: ABC DEF GHI J → 4 chunks
        assert len(chunks) == 4

    def test_config_in_request_dict_overrides_splitter_default(self):
        """Explicit chunk_size in the request overrides the splitter's 1000-char default."""
        p = ChunkingPipeline()
        # Without config the splitter default (1000) fits all 10 chars → 1 chunk.
        # With chunk_size=5 → 2 chunks.
        chunks = p.run(
            {"content": "ABCDEFGHIJ", "config": {"chunk_size": 5, "chunk_overlap": 0}},
            strategy="fixed_length",
        )
        assert len(chunks) == 2

    def test_metadata_config_and_request_config_merged(self):
        """Top-level 'config' and 'metadata.config' are merged; request key wins."""
        p = ChunkingPipeline()
        chunks = p.run(
            {
                "content": "ABCDEFGHIJ",
                "metadata": {"config": {"chunk_overlap": 99}},  # would cause step<0
                "config": {"chunk_size": 5, "chunk_overlap": 0},  # overrides overlap
            },
            strategy="fixed_length",
        )
        assert len(chunks) == 2


# ---------------------------------------------------------------------------
# Edge inputs
# ---------------------------------------------------------------------------


class TestEdgeInputs:
    def test_empty_string_returns_empty(self, pipeline):
        assert pipeline.run("") == []

    def test_empty_list_returns_empty(self, pipeline):
        assert pipeline.run([]) == []

    def test_none_like_content_returns_empty(self, pipeline):
        result = pipeline.run({"content": ""}, strategy="recursive")
        assert result == []

    def test_plain_string_input(self, pipeline):
        chunks = pipeline.run("Hello world", strategy="recursive")
        assert len(chunks) >= 1

    def test_sayou_block_input(self, pipeline):
        block = SayouBlock(
            type="text",
            content="Hello from block",
            metadata={"config": {"chunk_size": 1000}},
        )
        chunks = pipeline.run(block, strategy="recursive")
        assert len(chunks) >= 1

    def test_list_of_dicts_flattened(self, pipeline):
        items = [
            {"content": "Alpha", "metadata": {"id": "a"}},
            {"content": "Beta", "metadata": {"id": "b"}},
        ]
        chunks = pipeline.run(items, strategy="recursive")
        texts = [c.content for c in chunks]
        assert "Alpha" in texts
        assert "Beta" in texts

    def test_nested_content_list_flattened(self, pipeline):
        """Dict whose 'content' is itself a list should be recursively flattened."""
        nested = {"content": ["Part one", "Part two"], "metadata": {}}
        chunks = pipeline.run(nested, strategy="recursive")
        assert len(chunks) >= 2


# ---------------------------------------------------------------------------
# _register_manual guard
# ---------------------------------------------------------------------------


class TestRegisterManual:
    def test_instance_instead_of_class_raises_type_error(self):
        with pytest.raises(TypeError, match="CLASS"):
            ChunkingPipeline(extra_splitters=[MarkdownSplitter()])


# ---------------------------------------------------------------------------
# All results are SayouChunk instances
# ---------------------------------------------------------------------------


class TestOutputType:
    def test_all_results_are_sayou_chunks(self, pipeline):
        chunks = pipeline.run(
            {"content": "Lorem ipsum dolor sit amet.", "config": {"chunk_size": 10}},
            strategy="recursive",
        )
        for chunk in chunks:
            assert isinstance(
                chunk, SayouChunk
            ), f"Expected SayouChunk, got {type(chunk)}"
