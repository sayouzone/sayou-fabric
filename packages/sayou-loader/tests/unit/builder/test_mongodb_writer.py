"""
Unit tests for MongoDBWriter.
"""

import json
import logging
from unittest.mock import MagicMock, patch

import pytest


class TestMongoDBWriterCanHandle:
    def test_mongodb_strategy(self):
        from sayou.loader.plugins.mongodb_writer import MongoDBWriter

        assert MongoDBWriter.can_handle([], "mongodb://localhost", "mongodb") == 1.0

    def test_mongodb_uri(self):
        from sayou.loader.plugins.mongodb_writer import MongoDBWriter

        assert MongoDBWriter.can_handle([], "mongodb://host:27017/db", "auto") == 1.0

    def test_unknown_destination_returns_zero(self):
        from sayou.loader.plugins.mongodb_writer import MongoDBWriter

        assert MongoDBWriter.can_handle([], "file://out.json", "auto") == 0.0


class TestMongoDBWriterNormalise:
    def setup_method(self):
        from sayou.loader.plugins.mongodb_writer import MongoDBWriter

        self.writer = MongoDBWriter()
        self.writer.logger = logging.getLogger("test")
        self.writer._callbacks = []

    def test_dict_list_passthrough(self):
        result = self.writer._normalize_input_data([{"id": "1"}, {"id": "2"}])
        assert len(result) == 2

    def test_node_id_mapped_to_id(self):
        from sayou.core.schemas import SayouNode

        node = SayouNode(node_id="my-id", node_class="Entity", attributes={})
        result = self.writer._normalize_input_data([node])
        assert result[0]["id"] == "my-id"
