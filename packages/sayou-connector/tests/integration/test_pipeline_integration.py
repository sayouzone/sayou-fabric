"""
Integration tests for ConnectorPipeline.

These tests exercise the full pipeline (Generator → Fetcher → Packet)
against real file system and in-memory SQLite resources.

Marked with ``@pytest.mark.integration`` so they can be run separately:
    pytest -m integration
or excluded from the fast unit-test suite:
    pytest -m "not integration"
"""

import os

import pytest
from sayou.core.schemas import SayouPacket

from sayou.connector.pipeline import ConnectorPipeline

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def pipeline() -> ConnectorPipeline:
    return ConnectorPipeline()


# ---------------------------------------------------------------------------
# File strategy
# ---------------------------------------------------------------------------


class TestFileStrategy:
    def test_single_txt_file_fetched(self, pipeline, txt_file):
        packets = list(
            pipeline.run(
                source=os.path.dirname(txt_file), strategy="file", extensions=[".txt"]
            )
        )
        assert len(packets) == 1
        packet = packets[0]
        assert isinstance(packet, SayouPacket)
        assert packet.success is True
        assert packet.data == b"Hello Sayou"

    def test_packet_task_source_type_is_file(self, pipeline, txt_file):
        packets = list(
            pipeline.run(
                source=os.path.dirname(txt_file), strategy="file", extensions=[".txt"]
            )
        )
        assert packets[0].task.source_type == "file"

    def test_extension_filter_applied(self, pipeline, multi_file_dir):
        packets = list(
            pipeline.run(source=multi_file_dir, strategy="file", extensions=[".txt"])
        )
        for p in packets:
            assert p.task.uri.endswith(".txt")

    def test_multiple_files_all_fetched(self, pipeline, multi_file_dir):
        packets = list(
            pipeline.run(
                source=multi_file_dir, strategy="file", extensions=[".txt", ".md"]
            )
        )
        assert len(packets) == 3  # a.txt, b.txt, c.md

    def test_auto_strategy_detects_file_path(self, pipeline, txt_file):
        """auto strategy should resolve to FileGenerator for a local path."""
        packets = list(
            pipeline.run(
                source=os.path.dirname(txt_file), strategy="auto", extensions=[".txt"]
            )
        )
        assert len(packets) == 1
        assert packets[0].success is True

    def test_nonexistent_file_returns_failed_packet(self, pipeline, tmp_dir):
        """FileFetcher wraps FileNotFoundError → packet.success=False."""
        from sayou.core.schemas import SayouTask

        from sayou.connector.fetcher.file_fetcher import FileFetcher
        from sayou.connector.generator.file_generator import FileGenerator

        # Manually drive the fetcher with a bad path
        fetcher = FileFetcher()
        fetcher.FETCH_MAX_RETRIES = 1
        task = SayouTask(
            source_type="file", uri="/nonexistent/file.txt", params={}, meta={}
        )
        packet = fetcher.fetch(task)
        assert packet.success is False
        assert packet.error is not None


# ---------------------------------------------------------------------------
# SQLite strategy
# ---------------------------------------------------------------------------


class TestSqliteStrategy:
    BASE_QUERY = "SELECT * FROM data"
    BATCH = 10

    def test_full_pagination_yields_three_packets(self, pipeline, sqlite_db):
        """25 rows with batch_size=10 → 3 packets (10, 10, 5)."""
        packets = list(
            pipeline.run(
                source=sqlite_db,
                strategy="sqlite",
                query=self.BASE_QUERY,
                batch_size=self.BATCH,
            )
        )
        assert len(packets) == 3

    def test_first_packet_has_ten_rows(self, pipeline, sqlite_db):
        packets = list(
            pipeline.run(
                source=sqlite_db,
                strategy="sqlite",
                query=self.BASE_QUERY,
                batch_size=self.BATCH,
            )
        )
        assert len(packets[0].data) == 10

    def test_last_packet_has_five_rows(self, pipeline, sqlite_db):
        packets = list(
            pipeline.run(
                source=sqlite_db,
                strategy="sqlite",
                query=self.BASE_QUERY,
                batch_size=self.BATCH,
            )
        )
        assert len(packets[-1].data) == 5

    def test_offsets_are_sequential(self, pipeline, sqlite_db):
        packets = list(
            pipeline.run(
                source=sqlite_db,
                strategy="sqlite",
                query=self.BASE_QUERY,
                batch_size=self.BATCH,
            )
        )
        offsets = [p.task.meta["offset"] for p in packets]
        assert offsets == [0, 10, 20]

    def test_rows_are_dicts(self, pipeline, sqlite_db):
        packets = list(
            pipeline.run(
                source=sqlite_db,
                strategy="sqlite",
                query=self.BASE_QUERY,
                batch_size=self.BATCH,
            )
        )
        for packet in packets:
            for row in packet.data:
                assert isinstance(row, dict)

    def test_auto_strategy_detects_sqlite_uri(self, pipeline, sqlite_db):
        packets = list(
            pipeline.run(
                source=f"sqlite:///{sqlite_db}",
                strategy="auto",
                query=self.BASE_QUERY,
                batch_size=self.BATCH,
            )
        )
        assert len(packets) == 3

    def test_all_packets_successful(self, pipeline, sqlite_db):
        packets = list(
            pipeline.run(
                source=sqlite_db,
                strategy="sqlite",
                query=self.BASE_QUERY,
                batch_size=self.BATCH,
            )
        )
        assert all(p.success for p in packets)
