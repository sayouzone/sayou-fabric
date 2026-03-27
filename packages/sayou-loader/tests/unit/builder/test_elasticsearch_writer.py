"""
Unit tests for ElasticsearchWriter.
"""

import json
import logging
import pytest
from unittest.mock import MagicMock, patch


class TestElasticsearchWriterCanHandle:
    def test_elasticsearch_strategy(self):
        from sayou.loader.plugins.elasticsearch_writer import ElasticsearchWriter

        assert (
            ElasticsearchWriter.can_handle([], "http://host:9200/idx", "elasticsearch")
            == 1.0
        )

    def test_elasticsearch_uri(self):
        from sayou.loader.plugins.elasticsearch_writer import ElasticsearchWriter

        assert (
            ElasticsearchWriter.can_handle([], "elasticsearch://host:9200/idx", "auto")
            == 1.0
        )

    def test_unknown_returns_zero(self):
        from sayou.loader.plugins.elasticsearch_writer import ElasticsearchWriter

        assert ElasticsearchWriter.can_handle([], "s3://bucket", "auto") == 0.0


class TestElasticsearchBulkActions:
    def setup_method(self):
        from sayou.loader.plugins.elasticsearch_writer import ElasticsearchWriter

        self.writer = ElasticsearchWriter()
        self.writer.logger = logging.getLogger("test")
        self.writer._callbacks = []

    def test_generates_correct_action_format(self):
        actions = list(
            self.writer._generate_bulk_actions(
                [{"id": "doc1", "text": "hello"}], "my_index", "id"
            )
        )
        assert actions[0]["_index"] == "my_index"
        assert actions[0]["_id"] == "doc1"

    def test_missing_id_still_generates_action(self):
        actions = list(
            self.writer._generate_bulk_actions([{"text": "no id"}], "idx", "id")
        )
        assert len(actions) == 1
        assert "_id" not in actions[0]
