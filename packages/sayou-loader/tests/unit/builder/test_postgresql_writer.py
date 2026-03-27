"""
Unit tests for PostgresWriter.
"""

import json
import logging
import pytest
from unittest.mock import MagicMock, patch


class TestPostgresWriterCanHandle:
    def test_postgres_strategy(self):
        from sayou.loader.plugins.postgres_writer import PostgresWriter

        assert PostgresWriter.can_handle([], "postgresql://host/db", "postgres") == 1.0

    def test_postgresql_uri(self):
        from sayou.loader.plugins.postgres_writer import PostgresWriter

        assert PostgresWriter.can_handle([], "postgresql://host/db", "auto") == 1.0

    def test_postgres_uri_scheme(self):
        from sayou.loader.plugins.postgres_writer import PostgresWriter

        assert PostgresWriter.can_handle([], "postgres://host/db", "auto") == 1.0

    def test_unknown_returns_zero(self):
        from sayou.loader.plugins.postgres_writer import PostgresWriter

        assert PostgresWriter.can_handle([], "neo4j://host", "auto") == 0.0


class TestPostgresWriterNormalise:
    def setup_method(self):
        from sayou.loader.plugins.postgres_writer import PostgresWriter

        self.writer = PostgresWriter()
        self.writer.logger = logging.getLogger("test")
        self.writer._callbacks = []

    def test_dict_passthrough(self):
        result = self.writer._normalize_input_data([{"id": "1", "name": "Alice"}])
        assert result[0]["name"] == "Alice"

    def test_node_attributes_extracted(self):
        from sayou.core.schemas import SayouNode

        node = SayouNode(node_id="n1", node_class="Entity", attributes={"col1": "val1"})
        result = self.writer._normalize_input_data([node])
        assert result[0]["col1"] == "val1"
