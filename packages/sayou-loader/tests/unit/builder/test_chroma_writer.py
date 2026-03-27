"""
Unit tests for ChromaWriter.
"""

import json
import logging
import pytest
from unittest.mock import MagicMock, patch


class TestChromaWriterCanHandle:
    def test_chroma_strategy(self):
        from sayou.loader.plugins.chroma_writer import ChromaWriter

        assert ChromaWriter.can_handle([], "chroma://./db/col", "chroma") == 1.0

    def test_chroma_uri(self):
        from sayou.loader.plugins.chroma_writer import ChromaWriter

        assert ChromaWriter.can_handle([], "chroma://./mydb/collection", "auto") == 1.0

    def test_unknown_returns_zero(self):
        from sayou.loader.plugins.chroma_writer import ChromaWriter

        assert ChromaWriter.can_handle([], "mongodb://host", "auto") == 0.0


class TestChromaWriterSanitizeMetadata:
    def setup_method(self):
        from sayou.loader.plugins.chroma_writer import ChromaWriter

        self.writer = ChromaWriter()
        self.writer.logger = logging.getLogger("test")
        self.writer._callbacks = []

    def test_primitives_pass_through(self):
        meta = {"title": "Doc", "page": 1, "score": 0.9, "flag": True}
        assert self.writer._sanitize_metadata(meta) == meta

    def test_none_values_excluded(self):
        result = self.writer._sanitize_metadata({"title": "Doc", "empty": None})
        assert "empty" not in result

    def test_dict_value_json_serialised(self):
        result = self.writer._sanitize_metadata({"nested": {"a": 1}})
        assert json.loads(result["nested"])["a"] == 1


class TestChromaWriterParseDestination:
    def setup_method(self):
        from sayou.loader.plugins.chroma_writer import ChromaWriter

        self.writer = ChromaWriter()
        self.writer.logger = logging.getLogger("test")
        self.writer._callbacks = []

    def test_local_path_and_collection(self):
        path, col = self.writer._parse_destination("chroma://./mydb/my_collection")
        assert path == "./mydb"
        assert col == "my_collection"

    def test_bare_collection_name(self):
        _, col = self.writer._parse_destination("chroma://my_col")
        assert col == "my_col"
