"""
Integration tests for WrapperPipeline end-to-end flow.
"""

import pytest
from sayou.core.schemas import SayouOutput

from sayou.wrapper.adapter.document_chunk_adapter import DocumentChunkAdapter
from sayou.wrapper.pipeline import WrapperPipeline
from sayou.wrapper.plugins.embedding_adapter import EmbeddingAdapter
from sayou.wrapper.plugins.metadata_adapter import MetadataAdapter


def _chunk(content, **meta):
    return {"content": content, "metadata": meta}


class TestDocumentChunkFlow:
    def test_full_pipeline_document_chunk(self):
        pipeline = WrapperPipeline(extra_adapters=[DocumentChunkAdapter])
        chunks = [
            _chunk("Introduction paragraph.", chunk_id="c1", semantic_type="text"),
            _chunk("| Col1 | Col2 |", chunk_id="c2", semantic_type="table"),
            _chunk("def foo(): pass", chunk_id="c3", semantic_type="code_block"),
        ]
        output = pipeline.run(chunks, strategy="document_chunk")
        assert isinstance(output, SayouOutput)
        assert len(output.nodes) == 3

    def test_auto_strategy_selects_document_chunk(self):
        pipeline = WrapperPipeline(extra_adapters=[DocumentChunkAdapter])
        chunks = [_chunk("text", chunk_id="c1")]
        output = pipeline.run(chunks, strategy="document_chunk")
        assert len(output.nodes) == 1

    def test_parent_child_relationship_preserved(self):
        from sayou.core.ontology import SayouPredicate

        pipeline = WrapperPipeline(extra_adapters=[DocumentChunkAdapter])
        chunks = [
            _chunk("parent", chunk_id="parent-1"),
            _chunk("child", chunk_id="child-1", parent_id="parent-1"),
        ]
        output = pipeline.run(chunks, strategy="document_chunk")
        child_node = next(n for n in output.nodes if "child-1" in n.node_id)
        assert SayouPredicate.HAS_PARENT in child_node.relationships


class TestEmbeddingFlow:
    def test_stub_embedding_end_to_end(self):
        pipeline = WrapperPipeline(extra_adapters=[EmbeddingAdapter])
        items = [
            {"content": "First sentence.", "metadata": {"chunk_id": "e1"}},
            {"content": "Second sentence.", "metadata": {"chunk_id": "e2"}},
        ]
        output = pipeline.run(
            items, strategy="embedding", provider="stub", dimension=16
        )
        assert len(output.nodes) == 2
        for node in output.nodes:
            assert len(node.attributes.get("vector", [])) == 16

    def test_custom_fn_embedding(self):
        pipeline = WrapperPipeline(extra_adapters=[EmbeddingAdapter])
        fn = lambda texts: [[float(len(t))] * 4 for t in texts]
        items = [{"content": "hello", "metadata": {"chunk_id": "x"}}]
        output = pipeline.run(
            items, strategy="embedding", provider="external", embedding_fn=fn
        )
        assert output.nodes[0].attributes["vector"] == [5.0, 5.0, 5.0, 5.0]


class TestMetadataFlow:
    def test_metadata_enrichment(self):
        pipeline = WrapperPipeline(extra_adapters=[MetadataAdapter])
        items = [{"content": "hello world", "metadata": {"chunk_id": "m1"}}]
        output = pipeline.run(
            items,
            strategy="metadata",
            metadata_map={"word_count": lambda t: len(t.split())},
        )
        assert output.nodes[0].attributes.get("word_count") == 2

    def test_stub_mode(self):
        pipeline = WrapperPipeline(extra_adapters=[MetadataAdapter])
        items = [{"content": "test content", "metadata": {"chunk_id": "m2"}}]
        output = pipeline.run(items, strategy="metadata", use_stub=True)
        assert "summary" in output.nodes[0].attributes
