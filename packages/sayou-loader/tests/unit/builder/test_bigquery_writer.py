"""
Unit tests for BigQueryWriter.
"""

import json
import logging
import pytest
from unittest.mock import MagicMock, patch


class TestBigQueryWriterCanHandle:
    def test_bigquery_strategy(self):
        from sayou.loader.plugins.bigquery_writer import BigQueryWriter

        assert BigQueryWriter.can_handle([], "bq://proj.ds.tbl", "bigquery") == 1.0

    def test_bq_uri(self):
        from sayou.loader.plugins.bigquery_writer import BigQueryWriter

        assert (
            BigQueryWriter.can_handle([], "bq://project.dataset.table", "auto") == 1.0
        )

    def test_bigquery_uri(self):
        from sayou.loader.plugins.bigquery_writer import BigQueryWriter

        assert BigQueryWriter.can_handle([], "bigquery://proj.ds.tbl", "auto") == 1.0

    def test_unknown_returns_zero(self):
        from sayou.loader.plugins.bigquery_writer import BigQueryWriter

        assert BigQueryWriter.can_handle([], "file://out.json", "auto") == 0.0


class TestBigQueryWriterParseDestination:
    def setup_method(self):
        from sayou.loader.plugins.bigquery_writer import BigQueryWriter

        self.writer = BigQueryWriter()
        self.writer.logger = logging.getLogger("test")
        self.writer._callbacks = []

    def test_three_part_uri(self):
        proj, ds, tbl = self.writer._parse_destination(
            "bq://myproject.mydataset.mytable"
        )
        assert proj == "myproject" and ds == "mydataset" and tbl == "mytable"

    def test_kwargs_fallback(self):
        proj, ds, tbl = self.writer._parse_destination(
            "raw_table", bq_project_id="p", bq_dataset_id="d", bq_table_id="t"
        )
        assert proj == "p" and ds == "d" and tbl == "t"

    def test_invalid_destination_raises(self):
        with pytest.raises(ValueError):
            self.writer._parse_destination("not_a_uri")


class TestBigQueryTransformData:
    def setup_method(self):
        from sayou.loader.plugins.bigquery_writer import BigQueryWriter

        self.writer = BigQueryWriter()
        self.writer.logger = logging.getLogger("test")
        self.writer._callbacks = []

    def test_dict_list_converted_to_rows(self):
        rows = self.writer._transform_data(
            {"nodes": [{"node_id": "n1", "attributes": {"text": "hi"}}]}
        )
        assert rows[0]["node_id"] == "n1"

    def test_list_input_also_works(self):
        rows = self.writer._transform_data([{"node_id": "n2", "attributes": {}}])
        assert len(rows) == 1

    def test_empty_returns_empty(self):
        assert self.writer._transform_data({"nodes": []}) == []
