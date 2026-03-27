"""
Unit tests for VectorBuilder.
"""

import pytest
from sayou.core.schemas import SayouNode, SayouOutput

from sayou.assembler.builder.vector_builder import VectorBuilder


def _node(node_id, text="", vector=None):
    attrs = {"schema:text": text}
    if vector is not None:
        attrs["vector"] = vector
    return SayouNode(node_id=node_id, node_class="Node", attributes=attrs)


def _output(*nodes):
    return SayouOutput(nodes=list(nodes))


class TestCanHandle:
    def test_explicit_vector_strategy(self):
        assert VectorBuilder.can_handle(_output(), "vector") == 1.0

    def test_output_with_vector_attr_scores_high(self):
        n = _node("n1", vector=[0.1, 0.2])
        assert VectorBuilder.can_handle(_output(n)) >= 0.9

    def test_output_without_vector_returns_zero(self):
        assert VectorBuilder.can_handle(_output(_node("n1", text="hello"))) == 0.0


class TestDoBuild:
    def setup_method(self):
        import logging

        self.builder = VectorBuilder()
        self.builder.logger = logging.getLogger("test")
        self.builder._callbacks = []
        self.builder.embedding_fn = None

    def test_nodes_without_text_skipped(self):
        n = _node("n1", text="")
        result = self.builder._do_build(_output(n))
        assert len(result) == 0

    def test_node_id_preserved_in_payload(self):
        self.builder.embedding_fn = lambda t: [0.5] * 4
        n = _node("my-node", text="hello")
        result = self.builder._do_build(_output(n))
        assert result[0]["id"] == "my-node"

    def test_embedding_fn_called(self):
        calls = []

        def fn(t):
            calls.append(t)
            return [0.1] * 3

        self.builder.embedding_fn = fn
        n = _node("n1", text="embed me")
        self.builder._do_build(_output(n))
        assert calls == ["embed me"]

    def test_vector_in_payload(self):
        self.builder.embedding_fn = lambda t: [1.0, 2.0, 3.0]
        result = self.builder._do_build(_output(_node("n1", text="x")))
        assert result[0]["vector"] == [1.0, 2.0, 3.0]

    def test_no_embedding_fn_gives_empty_vector(self):
        result = self.builder._do_build(_output(_node("n1", text="x")))
        assert result[0]["vector"] == []

    def test_metadata_includes_node_class(self):
        self.builder.embedding_fn = lambda t: [0.0]
        n = SayouNode(
            node_id="n1", node_class="MyClass", attributes={"schema:text": "hello"}
        )
        result = self.builder._do_build(SayouOutput(nodes=[n]))
        assert result[0]["metadata"]["node_class"] == "MyClass"

    def test_multiple_nodes_produce_multiple_payloads(self):
        self.builder.embedding_fn = lambda t: [0.0] * 2
        nodes = [_node(f"n{i}", text=f"text {i}") for i in range(4)]
        result = self.builder._do_build(_output(*nodes))
        assert len(result) == 4
