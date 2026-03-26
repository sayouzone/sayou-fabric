"""
Integration tests for ChunkingPipeline.

Exercises the full pipeline (input normalisation → splitter resolution →
splitting → SayouChunk output) with realistic inputs.

Marked with ``@pytest.mark.integration``.
"""

import json

import pytest

from sayou.chunking.pipeline import ChunkingPipeline
from sayou.chunking.plugins.markdown_splitter import MarkdownSplitter
from sayou.chunking.plugins.code_splitter import CodeSplitter
from sayou.core.schemas import SayouChunk


pytestmark = pytest.mark.integration


@pytest.fixture
def pipeline() -> ChunkingPipeline:
    return ChunkingPipeline(extra_splitters=[MarkdownSplitter, CodeSplitter])


# ---------------------------------------------------------------------------
# End-to-end: text strategies
# ---------------------------------------------------------------------------


class TestTextStrategies:
    def test_recursive_on_long_text(self, pipeline):
        text = "Sentence number {}. ".format(0) * 100
        chunks = pipeline.run(
            {"content": text, "config": {"chunk_size": 100, "chunk_overlap": 0}},
            strategy="recursive",
        )
        assert len(chunks) > 1
        assert all(isinstance(c, SayouChunk) for c in chunks)

    def test_fixed_length_exact_reconstruction(self, pipeline):
        content = "A" * 100
        chunks = pipeline.run(
            {"content": content, "config": {"chunk_size": 25, "chunk_overlap": 0}},
            strategy="fixed_length",
        )
        assert len(chunks) == 4
        assert "".join(c.content for c in chunks) == content

    def test_parent_document_link_integrity(self, pipeline):
        text = "Word " * 300
        chunks = pipeline.run(
            {
                "content": text,
                "config": {
                    "parent_chunk_size": 200,
                    "chunk_size": 50,
                    "chunk_overlap": 0,
                },
            },
            strategy="parent_document",
        )
        parents = {
            c.metadata["chunk_id"]: c
            for c in chunks
            if c.metadata.get("doc_level") == "parent"
        }
        children = [c for c in chunks if c.metadata.get("doc_level") == "child"]

        assert len(parents) >= 1
        assert len(children) >= 1
        for child in children:
            assert child.metadata["parent_id"] in parents


# ---------------------------------------------------------------------------
# End-to-end: markdown
# ---------------------------------------------------------------------------


class TestMarkdownIntegration:
    def test_document_structure_preserved(self, pipeline):
        md = (
            "# Introduction\n"
            "This is the intro.\n\n"
            "## Background\n"
            "Some background text.\n\n"
            "## Methods\n"
            "Detailed methods here.\n"
        )
        chunks = pipeline.run(
            {"content": md, "config": {"chunk_size": 2000}}, strategy="markdown"
        )
        headers = [c for c in chunks if c.metadata.get("is_header")]
        assert len(headers) == 3

    def test_section_title_propagated_to_body(self, pipeline):
        md = "# My Section\nThis is body text."
        chunks = pipeline.run({"content": md}, strategy="markdown")
        body = [c for c in chunks if not c.metadata.get("is_header")]
        assert all(c.metadata.get("section_title") == "My Section" for c in body)


# ---------------------------------------------------------------------------
# End-to-end: code
# ---------------------------------------------------------------------------


class TestCodeIntegration:
    PYTHON_SRC = (
        "class Greeter:\n"
        "    def __init__(self, name: str):\n"
        "        self.name = name\n\n"
        "    def greet(self):\n"
        "        return f'Hello {self.name}'\n\n"
        "def main():\n"
        "    g = Greeter('World')\n"
        "    print(g.greet())\n"
    )

    def test_python_class_and_methods_chunked(self, pipeline):
        chunks = pipeline.run(
            {
                "content": self.PYTHON_SRC,
                "metadata": {"extension": ".py"},
                "config": {"chunk_size": 2000},
            },
            strategy="code",
        )
        method_names = {c.metadata.get("function_name") for c in chunks}
        assert "__init__" in method_names
        assert "greet" in method_names
        assert "main" in method_names

    def test_all_chunks_have_language_metadata(self, pipeline):
        chunks = pipeline.run(
            {
                "content": self.PYTHON_SRC,
                "metadata": {"extension": ".py"},
                "config": {"chunk_size": 2000},
            },
            strategy="code",
        )
        for chunk in chunks:
            assert chunk.metadata.get("language") == "python"


# ---------------------------------------------------------------------------
# End-to-end: JSON
# ---------------------------------------------------------------------------


class TestJsonIntegration:
    def test_list_split_and_reconstructed(self, pipeline):
        items = [{"id": i, "value": f"item_{i}"} for i in range(30)]
        content = json.dumps(items)
        chunks = pipeline.run(
            {
                "content": content,
                "config": {"chunk_size": 200},
            },
            strategy="json",
        )
        assert len(chunks) > 1
        total = sum(c.metadata["item_count"] for c in chunks)
        assert total == 30

    def test_serialised_content_is_valid_json(self, pipeline):
        data = {"key": [1, 2, 3], "other": "value"}
        chunks = pipeline.run(
            {"content": json.dumps(data), "config": {"chunk_size": 500}},
            strategy="json",
        )
        for chunk in chunks:
            parsed = json.loads(chunk.content)
            assert isinstance(parsed, (dict, list))


# ---------------------------------------------------------------------------
# End-to-end: multi-block input
# ---------------------------------------------------------------------------


class TestMultiBlockInput:
    def test_multiple_blocks_produce_independent_chunks(self, pipeline):
        blocks = [
            {"content": "Block one content.", "metadata": {"id": "b1"}},
            {"content": "Block two content.", "metadata": {"id": "b2"}},
            {"content": "Block three content.", "metadata": {"id": "b3"}},
        ]
        chunks = pipeline.run(blocks, strategy="recursive")
        assert len(chunks) >= 3

    def test_model_dump_works_on_all_chunks(self, pipeline):
        """Ensure every output chunk is a valid Pydantic model."""
        chunks = pipeline.run(
            {
                "content": "Test content for serialisation.",
                "config": {"chunk_size": 1000},
            },
            strategy="recursive",
        )
        for chunk in chunks:
            dumped = chunk.model_dump()
            assert "content" in dumped
            assert "metadata" in dumped
