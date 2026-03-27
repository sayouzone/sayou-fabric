"""
Unit tests for DocumentChunkAdapter.
"""

import pytest
from sayou.core.schemas import SayouOutput

from sayou.wrapper.adapter.document_chunk_adapter import DocumentChunkAdapter


def _chunk(content="Hello", **meta):
    return {"content": content, "metadata": meta}


class TestCanHandle:
    def test_explicit_strategy_returns_1(self):
        assert DocumentChunkAdapter.can_handle([], "document_chunk") == 1.0

    def test_list_with_chunk_id_scores_high(self):
        data = [{"chunk_id": "c1", "content": "x"}]
        assert DocumentChunkAdapter.can_handle(data) >= 0.9

    def test_empty_list_scores_low(self):
        assert DocumentChunkAdapter.can_handle([]) == 0.1

    def test_unknown_type_returns_zero(self):
        assert DocumentChunkAdapter.can_handle("plain string") == 0.0


class TestDoAdapt:
    def setup_method(self):
        self.adapter = DocumentChunkAdapter()
        self.adapter.logger = __import__("logging").getLogger("test")
        self.adapter._callbacks = []
        self.adapter.config = {}

    def test_single_chunk_wrapped_in_list(self):
        output = self.adapter._do_adapt(_chunk("hello", chunk_id="c1"))
        assert len(output.nodes) == 1

    def test_node_id_uses_chunk_id(self):
        output = self.adapter._do_adapt([_chunk("hi", chunk_id="abc123")])
        assert "abc123" in output.nodes[0].node_id

    def test_node_id_falls_back_to_md5_when_no_chunk_id(self):
        output = self.adapter._do_adapt([_chunk("deterministic")])
        assert "sayou:doc:" in output.nodes[0].node_id

    def test_source_name_included_in_node_id(self):
        output = self.adapter._do_adapt(
            [_chunk("x", chunk_id="c1", source="report.pdf")]
        )
        assert "report.pdf" in output.nodes[0].node_id

    def test_text_class_for_default_semantic_type(self):
        from sayou.core.ontology import SayouClass

        output = self.adapter._do_adapt([_chunk("text")])
        assert output.nodes[0].node_class == SayouClass.TEXT

    def test_topic_class_for_header(self):
        from sayou.core.ontology import SayouClass

        output = self.adapter._do_adapt([_chunk("Header", is_header=True)])
        assert output.nodes[0].node_class == SayouClass.TOPIC

    def test_table_class_for_table_semantic_type(self):
        from sayou.core.ontology import SayouClass

        output = self.adapter._do_adapt([_chunk("| a | b |", semantic_type="table")])
        assert output.nodes[0].node_class == SayouClass.TABLE

    def test_parent_relationship_added(self):
        from sayou.core.ontology import SayouPredicate

        output = self.adapter._do_adapt(
            [_chunk("child", chunk_id="c2", parent_id="c1")]
        )
        rels = output.nodes[0].relationships
        assert SayouPredicate.HAS_PARENT in rels

    def test_invalid_item_skipped(self):
        output = self.adapter._do_adapt(["not_a_dict"])
        assert len(output.nodes) == 0

    def test_multiple_chunks_produce_multiple_nodes(self):
        chunks = [_chunk(f"chunk {i}", chunk_id=f"c{i}") for i in range(5)]
        output = self.adapter._do_adapt(chunks)
        assert len(output.nodes) == 5

    def test_output_metadata_source(self):
        output = self.adapter._do_adapt([_chunk("x")])
        assert output.metadata.get("source") == "sayou-chunking"
