"""
Unit tests for EmbeddingAdapter.
"""

import pytest
from sayou.core.schemas import SayouOutput

from sayou.wrapper.plugins.embedding_adapter import EmbeddingAdapter


def _items(*contents):
    return [
        {"content": c, "metadata": {"chunk_id": f"c{i}"}}
        for i, c in enumerate(contents)
    ]


class TestCanHandle:
    def test_explicit_embedding_strategy(self):
        assert EmbeddingAdapter.can_handle([], "embedding") == 1.0

    def test_explicit_vector_strategy(self):
        assert EmbeddingAdapter.can_handle([], "vector") == 1.0

    def test_list_of_content_dicts_scores_high(self):
        data = [{"content": "hello"}]
        assert EmbeddingAdapter.can_handle(data, "auto") == 0.8

    def test_unrecognised_data_returns_zero(self):
        assert EmbeddingAdapter.can_handle("plain string", "auto") == 0.0


class TestDoAdapt:
    def setup_method(self):
        self.adapter = EmbeddingAdapter()
        self.adapter.logger = __import__("logging").getLogger("test")
        self.adapter._callbacks = []
        self.adapter.config = {}

    def test_stub_provider_attaches_vectors(self):
        items = _items("hello", "world")
        output = self.adapter._do_adapt(items, provider="stub", dimension=8)
        for node in output.nodes:
            assert "vector" in node.attributes
            assert len(node.attributes["vector"]) == 8

    def test_custom_embedding_fn_used(self):
        fn = lambda texts: [[0.1] * 4 for _ in texts]
        items = _items("a", "b")
        output = self.adapter._do_adapt(items, provider="external", embedding_fn=fn)
        assert output.nodes[0].attributes["vector"] == [0.1] * 4

    def test_external_provider_without_client_raises(self):
        items = _items("x")
        with pytest.raises(ValueError, match="neither 'client' nor"):
            self.adapter._do_adapt(items, provider="external")

    def test_node_count_matches_input(self):
        items = _items("a", "b", "c")
        output = self.adapter._do_adapt(items, provider="stub", dimension=4)
        assert len(output.nodes) == 3

    def test_empty_content_skips_embedding(self):
        items = [{"content": "", "metadata": {"chunk_id": "empty"}}]
        output = self.adapter._do_adapt(items, provider="stub", dimension=4)
        # Node is created but no vector attached (empty content skipped)
        assert "vector" not in output.nodes[0].attributes

    def test_node_ids_taken_from_chunk_id(self):
        items = [{"content": "x", "metadata": {"chunk_id": "myid"}}]
        output = self.adapter._do_adapt(items, provider="stub", dimension=4)
        assert output.nodes[0].node_id == "myid"

    def test_unknown_provider_falls_back_to_stub(self):
        items = _items("x")
        # Should not raise; falls back with a warning log
        output = self.adapter._do_adapt(items, provider="bogus", dimension=4)
        assert "vector" in output.nodes[0].attributes


class TestEmbedViaClient:
    def setup_method(self):
        self.adapter = EmbeddingAdapter()
        self.adapter.logger = __import__("logging").getLogger("test")
        self.adapter._callbacks = []

    def test_embed_documents_client(self):
        client = type(
            "C", (), {"embed_documents": lambda self, t: [[0.5] * 3 for _ in t]}
        )()
        result = self.adapter._embed_via_client(client, ["hello"])
        assert result == [[0.5, 0.5, 0.5]]

    def test_unsupported_client_raises(self):
        client = object()
        with pytest.raises(ValueError, match="Unsupported client"):
            self.adapter._embed_via_client(client, ["x"])
