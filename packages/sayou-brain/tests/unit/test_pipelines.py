"""
Unit tests for all Brain pipelines.

Tests are isolated from sub-libraries via conftest stubs.
Each pipeline is verified for:
- Construction and sub-pipeline registration
- Callback propagation
- Empty / failed packet handling
- Stats dict structure
- process() facade
"""

import logging
from unittest.mock import MagicMock, call, patch

import pytest
from sayou.core.schemas import SayouOutput, SayouPacket

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _packet(data=b"raw bytes", success=True, error=None):
    from sayou.core.schemas import SayouPacket

    p = SayouPacket(data=data, success=success, error=error)
    p.task = MagicMock()
    p.task.uri = "file://test.txt"
    p.task.meta = {"filename": "test.txt"}
    p.meta = {}
    return p


def _setup_connector(pipeline_obj, packets):
    """Make the connector stub return a list of packets."""
    pipeline_obj.connector.run.return_value = packets


# ---------------------------------------------------------------------------
# BypassPipeline
# ---------------------------------------------------------------------------


class TestBypassPipeline:
    def setup_method(self):
        from sayou.brain.pipelines.bypass import BypassPipeline

        self.cls = BypassPipeline
        self.p = BypassPipeline()

    def test_sub_pipelines_registered(self):
        assert "connector" in self.p._sub_pipelines
        assert "loader" in self.p._sub_pipelines

    def test_no_refinery_or_chunking(self):
        assert "refinery" not in self.p._sub_pipelines
        assert "chunking" not in self.p._sub_pipelines

    def test_requires_destination(self):
        with pytest.raises(ValueError):
            self.p.ingest("src://x", destination=None)

    def test_empty_packets_returns_zero_stats(self):
        _setup_connector(self.p, [])
        stats = self.p.ingest("src://x", destination="./out/")
        assert stats["read"] == 0 and stats["written"] == 0

    def test_failed_packet_counted(self):
        _setup_connector(self.p, [_packet(success=False, error="fetch err")])
        self.p.loader.run.return_value = True
        stats = self.p.ingest("src://x", destination="./out/")
        assert stats["failed"] == 1
        assert stats["written"] == 0

    def test_successful_packet_written(self):
        _setup_connector(self.p, [_packet(data=b"hello")])
        self.p.loader.run.return_value = True
        stats = self.p.ingest("src://x", destination="./out/")
        assert stats["read"] == 1
        assert stats["written"] == 1

    def test_loader_false_counted_as_failed(self):
        _setup_connector(self.p, [_packet()])
        self.p.loader.run.return_value = False
        stats = self.p.ingest("src://x", destination="./out/")
        assert stats["failed"] == 1
        assert stats["written"] == 0

    def test_data_written_verbatim(self):
        raw = b"\x89PNG raw bytes"
        _setup_connector(self.p, [_packet(data=raw)])
        self.p.loader.run.return_value = True
        self.p.ingest("src://x", destination="./out/")
        call_args = self.p.loader.run.call_args
        assert call_args.kwargs.get("input_data") == raw or (
            call_args.args and call_args.args[0] == raw
        )

    def test_callback_propagated(self):
        cb = MagicMock()
        self.p.add_callback(cb)
        assert cb in self.p.connector._callbacks or self.p.connector.add_callback.called

    def test_process_facade(self):
        with patch.object(
            self.cls, "ingest", return_value={"read": 1, "written": 1, "failed": 0}
        ) as m:
            result = self.cls.process("src://x", destination="./out/")
        m.assert_called_once()
        assert result["written"] == 1

    def test_multiple_packets_all_written(self):
        packets = [_packet(data=f"item{i}".encode()) for i in range(5)]
        _setup_connector(self.p, packets)
        self.p.loader.run.return_value = True
        stats = self.p.ingest("src://x", destination="./out/")
        assert stats["read"] == 5
        assert stats["written"] == 5


# ---------------------------------------------------------------------------
# TransferPipeline
# ---------------------------------------------------------------------------


class TestTransferPipeline:
    def setup_method(self):
        from sayou.brain.pipelines.transfer import TransferPipeline

        self.cls = TransferPipeline
        self.p = TransferPipeline()

    def test_sub_pipelines_registered(self):
        assert "connector" in self.p._sub_pipelines
        assert "refinery" in self.p._sub_pipelines
        assert "loader" in self.p._sub_pipelines

    def test_requires_destination(self):
        with pytest.raises(ValueError):
            self.p.ingest("src://x", destination=None)

    def test_successful_transfer(self):
        _setup_connector(self.p, [_packet(data={"records": [1, 2, 3]})])
        self.p.loader.run.return_value = True
        stats = self.p.ingest("src://x", destination="./out/")
        assert stats["read"] == 1
        assert stats["written"] == 1

    def test_refinery_used_when_flag_set(self):
        _setup_connector(self.p, [_packet(data="raw text")])
        self.p.refinery.run.return_value = "refined"
        self.p.loader.run.return_value = True
        self.p.ingest("src://x", destination="./out/", use_refinery=True)
        self.p.refinery.run.assert_called_once()

    def test_refinery_not_called_by_default(self):
        _setup_connector(self.p, [_packet()])
        self.p.loader.run.return_value = True
        self.p.refinery.run.reset_mock()
        self.p.ingest("src://x", destination="./out/")
        self.p.refinery.run.assert_not_called()

    def test_stats_structure(self):
        _setup_connector(self.p, [])
        stats = self.p.ingest("src://x", destination="./out/")
        assert set(stats.keys()) == {"read", "written", "failed"}


# ---------------------------------------------------------------------------
# StructurePipeline
# ---------------------------------------------------------------------------


class TestStructurePipeline:
    def setup_method(self):
        from sayou.brain.pipelines.structure import StructurePipeline

        self.cls = StructurePipeline
        self.p = StructurePipeline()

    def test_sub_pipelines_registered(self):
        for key in ("connector", "chunking", "wrapper", "assembler", "loader"):
            assert key in self.p._sub_pipelines

    def test_no_nodes_aborts_assembly(self):
        _setup_connector(self.p, [_packet(data={"content": "", "meta": {}})])
        self.p.chunking.run.return_value = []
        self.p.wrapper.run.return_value = SayouOutput(nodes=[])
        stats = self.p.ingest("src://x", destination="./out/")
        self.p.assembler.run.assert_not_called()
        assert stats["saved"] == 0

    def test_stats_structure(self):
        _setup_connector(self.p, [])
        stats = self.p.ingest("src://x", destination="./out/")
        assert set(stats.keys()) >= {"extracted", "chunks", "nodes", "edges", "saved"}


# ---------------------------------------------------------------------------
# NormalPipeline
# ---------------------------------------------------------------------------


class TestNormalPipeline:
    def setup_method(self):
        from sayou.brain.pipelines.normal import NormalPipeline

        self.cls = NormalPipeline
        self.p = NormalPipeline()

    def test_has_refinery_stage(self):
        assert "refinery" in self.p._sub_pipelines

    def test_refinery_called_per_packet(self):
        _setup_connector(self.p, [_packet(data="text"), _packet(data="more")])
        self.p.refinery.run.reset_mock()
        self.p.refinery.run.return_value = MagicMock()
        self.p.chunking.run.return_value = []
        self.p.ingest("src://x", destination="./out/")
        assert self.p.refinery.run.call_count == 2

    def test_stats_structure(self):
        _setup_connector(self.p, [])
        stats = self.p.ingest("src://x", destination="./out/")
        assert set(stats.keys()) >= {"extracted", "chunks", "nodes", "edges", "saved"}


# ---------------------------------------------------------------------------
# StandardPipeline
# ---------------------------------------------------------------------------


class TestStandardPipeline:
    def setup_method(self):
        from sayou.brain.pipelines.standard import StandardPipeline

        self.cls = StandardPipeline
        self.p = StandardPipeline()

    def test_all_sub_pipelines_registered(self):
        for key in (
            "connector",
            "document",
            "refinery",
            "chunking",
            "wrapper",
            "assembler",
            "loader",
        ):
            assert key in self.p._sub_pipelines

    def test_default_destination_set_when_missing(self):
        """Pipeline should not raise when destination is None."""
        _setup_connector(self.p, [])
        stats = self.p.ingest("source.pdf", destination=None)
        assert isinstance(stats, dict)

    def test_failed_packet_increments_failed(self):
        _setup_connector(
            self.p,
            [
                _packet(success=False, error="timeout"),
                _packet(success=True, data=b"ok"),
            ],
        )
        self.p.document.run.return_value = None
        self.p.refinery.run.return_value = []
        stats = self.p.ingest("src://x", destination="./out/")
        assert stats["failed"] >= 1

    def test_stats_structure(self):
        _setup_connector(self.p, [])
        stats = self.p.ingest("src://x", destination="./out/")
        assert set(stats.keys()) >= {"processed", "failed", "files_count"}


# ---------------------------------------------------------------------------
# BaseBrainPipeline shared behaviour
# ---------------------------------------------------------------------------


class TestBaseBrainShared:
    def test_config_section_access(self):
        from sayou.brain.pipelines.bypass import BypassPipeline

        p = BypassPipeline(config={"loader": {"batch_size": 256}})
        assert p.config.loader == {"batch_size": 256}

    def test_config_merge_via_kwargs(self):
        from sayou.brain.pipelines.bypass import BypassPipeline

        p = BypassPipeline(timeout=30)
        assert p.config._config.get("timeout") == 30

    def test_sanitize_filename(self):
        from sayou.brain.pipelines.bypass import BypassPipeline

        p = BypassPipeline()
        assert p._sanitize_filename('bad/name:file"test') == "bad_name_file_test"
