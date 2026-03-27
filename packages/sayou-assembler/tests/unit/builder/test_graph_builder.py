"""
Unit tests for GraphBuilder.
"""

import pytest
from sayou.core.schemas import SayouNode, SayouOutput

from sayou.assembler.builder.graph_builder import GraphBuilder


def _node(node_id, cls="Node", relationships=None):
    return SayouNode(
        node_id=node_id,
        node_class=cls,
        attributes={},
        relationships=relationships or {},
    )


def _output(*nodes):
    return SayouOutput(nodes=list(nodes))


class TestCanHandle:
    def test_explicit_graph_strategy(self):
        assert GraphBuilder.can_handle(_output(), "graph") == 1.0

    def test_explicit_hierarchy_strategy(self):
        assert GraphBuilder.can_handle(_output(), "hierarchy") == 1.0

    def test_sayou_output_scores_high(self):
        assert GraphBuilder.can_handle(_output(_node("n1"))) >= 0.9

    def test_dict_with_nodes_scores_high(self):
        assert GraphBuilder.can_handle({"nodes": []}) >= 0.9

    def test_unknown_returns_zero(self):
        assert GraphBuilder.can_handle("plain string") == 0.0


class TestDoBuild:
    def setup_method(self):
        import logging

        self.builder = GraphBuilder()
        self.builder.logger = logging.getLogger("test")
        self.builder._callbacks = []

    def test_single_node_in_output(self):
        result = self.builder._do_build(_output(_node("n1")))
        assert len(result["nodes"]) == 1

    def test_node_relationships_excluded_from_node_props(self):
        n = _node("n1", relationships={"sayou:hasParent": ["n0"]})
        result = self.builder._do_build(_output(n))
        # Node dict should not contain relationships key
        assert "relationships" not in result["nodes"][0]

    def test_forward_edge_created(self):
        n = _node("child", relationships={"sayou:hasParent": ["parent"]})
        result = self.builder._do_build(_output(n))
        forward = [e for e in result["edges"] if not e.get("is_reverse")]
        assert any(e["source"] == "child" and e["target"] == "parent" for e in forward)

    def test_reverse_edge_created(self):
        n = _node("child", relationships={"sayou:hasParent": ["parent"]})
        result = self.builder._do_build(_output(n))
        reverse = [e for e in result["edges"] if e.get("is_reverse")]
        assert any(e["source"] == "parent" and e["target"] == "child" for e in reverse)

    def test_has_parent_reverse_is_has_child(self):
        n = _node("child", relationships={"sayou:hasParent": ["parent"]})
        result = self.builder._do_build(_output(n))
        rev = next(e for e in result["edges"] if e.get("is_reverse"))
        assert rev["type"] == "sayou:hasChild"

    def test_stats_populated(self):
        result = self.builder._do_build(_output(_node("n1"), _node("n2")))
        assert result["stats"]["node_count"] == 2
        assert result["stats"]["edge_count"] == 0  # no relationships

    def test_multiple_targets_per_relationship(self):
        n = _node("src", relationships={"sayou:hasParent": ["p1", "p2"]})
        result = self.builder._do_build(_output(n))
        # 2 forward + 2 reverse = 4 edges
        assert len(result["edges"]) == 4


class TestGetReverseType:
    def setup_method(self):
        self.builder = GraphBuilder()

    def test_has_parent_gives_has_child(self):
        assert self.builder._get_reverse_type("sayou:hasParent") == "sayou:hasChild"

    def test_belongs_to_gives_contains(self):
        assert self.builder._get_reverse_type("sayou:belongsTo") == "sayou:contains"

    def test_next_gives_previous(self):
        assert self.builder._get_reverse_type("sayou:next") == "sayou:previous"

    def test_unknown_gets_rev_suffix(self):
        assert self.builder._get_reverse_type("sayou:foo") == "sayou:foo_REV"
