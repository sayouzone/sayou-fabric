"""
Unit tests for Neo4jWriter.
"""

import json
import logging
import pytest
from unittest.mock import MagicMock, patch


class TestNeo4jWriterCanHandle:
    def test_neo4j_strategy(self):
        from sayou.loader.plugins.neo4j_writer import Neo4jWriter

        with patch("sayou.loader.plugins.neo4j_writer.GraphDatabase", MagicMock()):
            assert Neo4jWriter.can_handle([], "bolt://localhost:7687", "neo4j") == 1.0

    def test_bolt_destination(self):
        from sayou.loader.plugins.neo4j_writer import Neo4jWriter

        with patch("sayou.loader.plugins.neo4j_writer.GraphDatabase", MagicMock()):
            assert Neo4jWriter.can_handle([], "bolt://localhost:7687", "auto") == 1.0

    def test_returns_zero_when_neo4j_not_installed(self):
        from sayou.loader.plugins.neo4j_writer import Neo4jWriter

        with patch("sayou.loader.plugins.neo4j_writer.GraphDatabase", None):
            assert Neo4jWriter.can_handle([], "bolt://localhost", "auto") == 0.0


class TestNeo4jWriterSanitizeProps:
    def setup_method(self):
        from sayou.loader.plugins.neo4j_writer import Neo4jWriter

        self.writer = Neo4jWriter()
        self.writer.logger = logging.getLogger("test")
        self.writer._callbacks = []

    def test_primitive_values_pass_through(self):
        props = {"name": "Alice", "age": 30, "score": 9.5, "active": True}
        assert self.writer._sanitize_props(props) == props

    def test_links_key_excluded(self):
        result = self.writer._sanitize_props({"id": "n1", "links": [{"target": "n2"}]})
        assert "links" not in result

    def test_dict_value_json_serialised(self):
        result = self.writer._sanitize_props({"meta": {"source": "file"}})
        assert json.loads(result["meta"])["source"] == "file"

    def test_primitive_list_preserved(self):
        result = self.writer._sanitize_props({"tags": ["a", "b", "c"]})
        assert result["tags"] == ["a", "b", "c"]

    def test_mixed_list_json_serialised(self):
        result = self.writer._sanitize_props({"data": [{"x": 1}, "str"]})
        assert isinstance(result["data"], str)


class TestNeo4jWriterNormalise:
    def setup_method(self):
        from sayou.loader.plugins.neo4j_writer import Neo4jWriter

        self.writer = Neo4jWriter()
        self.writer.logger = logging.getLogger("test")
        self.writer._callbacks = []

    def test_dict_passthrough(self):
        result = self.writer._normalize_input_data([{"id": "n1", "name": "Alice"}])
        assert result[0]["id"] == "n1"

    def test_sayou_node_normalised(self):
        from sayou.core.schemas import SayouNode

        node = SayouNode(
            node_id="n1", node_class="Person", attributes={"schema:text": "hello"}
        )
        result = self.writer._normalize_input_data([node])
        assert result[0]["id"] == "n1"
