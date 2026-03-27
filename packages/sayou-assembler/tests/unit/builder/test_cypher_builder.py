"""
Unit tests for CypherBuilder.
"""

import pytest
from sayou.core.schemas import SayouNode, SayouOutput

from sayou.assembler.plugins.cypher_builder import CypherBuilder


def _node(node_id, cls="Node", attrs=None, rels=None):
    return SayouNode(
        node_id=node_id,
        node_class=cls,
        friendly_name=f"Node {node_id}",
        attributes=attrs or {},
        relationships=rels or {},
    )


def _output(*nodes):
    return SayouOutput(nodes=list(nodes))


class TestCanHandle:
    def test_cypher_strategy(self):
        assert CypherBuilder.can_handle(_output(), "cypher") == 1.0

    def test_neo4j_strategy(self):
        assert CypherBuilder.can_handle(_output(), "neo4j") == 1.0

    def test_auto_returns_zero(self):
        assert CypherBuilder.can_handle(_output(), "auto") == 0.0


class TestDoBuild:
    def setup_method(self):
        import logging

        self.builder = CypherBuilder()
        self.builder.logger = logging.getLogger("test")
        self.builder._callbacks = []

    def test_merge_query_generated_per_node(self):
        queries = self.builder._do_build(_output(_node("n1"), _node("n2")))
        merge_queries = [q for q in queries if q.startswith("MERGE")]
        assert len(merge_queries) == 2

    def test_merge_includes_node_id(self):
        queries = self.builder._do_build(_output(_node("node-abc")))
        assert any("node-abc" in q for q in queries)

    def test_relationship_query_generated(self):
        n = _node("src", rels={"KNOWS": ["tgt"]})
        queries = self.builder._do_build(_output(n, _node("tgt")))
        match_queries = [q for q in queries if "MATCH" in q]
        assert len(match_queries) >= 1

    def test_colon_in_label_replaced(self):
        n = _node("n1", cls="sayou:Text")
        queries = self.builder._do_build(_output(n))
        # colons in labels must be replaced
        assert "sayou_Text" in queries[0]

    def test_string_relationship_target_handled(self):
        """relationships with a bare string (not list) must not crash."""
        n = _node("src", rels={"REL": "tgt"})
        queries = self.builder._do_build(_output(n))
        # Should produce at least the node MERGE
        assert any("src" in q for q in queries)


class TestHelpers:
    def setup_method(self):
        self.builder = CypherBuilder()

    def test_clean_label_replaces_colon(self):
        assert self.builder._clean_label("sayou:Text") == "sayou_Text"

    def test_clean_label_no_colon(self):
        assert self.builder._clean_label("Entity") == "Entity"

    def test_dict_to_cypher_props_is_json(self):
        import json

        props = {"name": "Alice", "age": 30}
        result = self.builder._dict_to_cypher_props(props)
        parsed = json.loads(result)
        assert parsed["name"] == "Alice"
