"""
Integration tests for LoaderPipeline end-to-end.
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest
from sayou.core.schemas import SayouNode, SayouOutput

from sayou.loader.pipeline import LoaderPipeline
from sayou.loader.writer.console_writer import ConsoleWriter
from sayou.loader.writer.file_writer import FileWriter
from sayou.loader.writer.jsonl_writer import JsonLineWriter


def _nodes(*ids):
    return [
        SayouNode(
            node_id=nid,
            node_class="Node",
            attributes={"schema:text": f"content of {nid}"},
        )
        for nid in ids
    ]


# ---------------------------------------------------------------------------
# FileWriter integration
# ---------------------------------------------------------------------------


class TestFileWriterIntegration:
    def test_write_dict_to_json_file(self, tmp_path):
        pipeline = LoaderPipeline(extra_writers=[FileWriter])
        dest = str(tmp_path / "out.json")
        data = {"nodes": [{"id": "n1"}], "edges": []}
        result = pipeline.run(data, dest, strategy="FileWriter")
        assert result is True
        with open(dest) as f:
            assert json.load(f)["nodes"][0]["id"] == "n1"

    def test_write_string_to_txt_file(self, tmp_path):
        pipeline = LoaderPipeline(extra_writers=[FileWriter])
        dest = str(tmp_path / "out.txt")
        result = pipeline.run("hello world", dest, strategy="FileWriter")
        assert result is True
        assert open(dest).read() == "hello world"

    def test_auto_strategy_selects_file_writer(self, tmp_path):
        pipeline = LoaderPipeline(extra_writers=[FileWriter])
        dest = str(tmp_path / "data.json")
        result = pipeline.run({"x": 1}, dest, strategy="auto")
        assert result is True
        assert os.path.exists(dest)

    def test_empty_input_returns_true_without_writing(self, tmp_path):
        pipeline = LoaderPipeline(extra_writers=[FileWriter])
        dest = str(tmp_path / "never.json")
        result = pipeline.run(None, dest, strategy="FileWriter")
        assert result is True
        assert not os.path.exists(dest)


# ---------------------------------------------------------------------------
# JsonLineWriter integration
# ---------------------------------------------------------------------------


class TestJsonLineWriterIntegration:
    def test_writes_records_as_jsonl(self, tmp_path):
        pipeline = LoaderPipeline(extra_writers=[JsonLineWriter])
        dest = str(tmp_path / "records.jsonl")
        data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        result = pipeline.run(data, dest, strategy="JsonLineWriter")
        assert result is True
        lines = open(dest).read().strip().splitlines()
        assert len(lines) == 2
        assert json.loads(lines[1])["name"] == "Bob"

    def test_auto_selects_jsonl_for_dotjsonl_destination(self, tmp_path):
        pipeline = LoaderPipeline(extra_writers=[JsonLineWriter])
        dest = str(tmp_path / "output.jsonl")
        data = [{"k": "v"}]
        pipeline.run(data, dest, strategy="auto")
        assert os.path.exists(dest)


# ---------------------------------------------------------------------------
# ConsoleWriter integration
# ---------------------------------------------------------------------------


class TestConsoleWriterIntegration:
    def test_console_writer_selected_by_strategy(self, capsys):
        pipeline = LoaderPipeline(extra_writers=[ConsoleWriter])
        result = pipeline.run({"msg": "hello"}, "stdout", strategy="ConsoleWriter")
        assert result is True
        out = capsys.readouterr().out
        assert "hello" in out

    def test_auto_selects_console_for_stdout_destination(self, capsys):
        pipeline = LoaderPipeline(extra_writers=[ConsoleWriter])
        pipeline.run({"x": 1}, "stdout", strategy="auto")
        out = capsys.readouterr().out
        assert "ConsoleWriter" in out or "x" in out


# ---------------------------------------------------------------------------
# Multi-writer pipeline
# ---------------------------------------------------------------------------


class TestMultiWriterPipeline:
    def test_explicit_strategy_selects_correct_writer(self, tmp_path):
        pipeline = LoaderPipeline(
            extra_writers=[FileWriter, JsonLineWriter, ConsoleWriter]
        )

        # JSONL writer selected by name
        dest = str(tmp_path / "out.jsonl")
        pipeline.run([{"id": "x"}], dest, strategy="JsonLineWriter")
        assert os.path.exists(dest)

    def test_file_writer_selected_by_extension(self, tmp_path):
        pipeline = LoaderPipeline(extra_writers=[FileWriter, JsonLineWriter])
        dest = str(tmp_path / "result.json")
        pipeline.run({"a": 1}, dest, strategy="auto")
        assert os.path.exists(dest)


# ---------------------------------------------------------------------------
# Neo4jWriter (mocked)
# ---------------------------------------------------------------------------


class TestNeo4jWriterIntegration:
    def test_neo4j_writer_routes_correctly(self):
        from sayou.loader.plugins.neo4j_writer import Neo4jWriter

        mock_gdb = MagicMock()
        mock_session = MagicMock()
        mock_gdb.return_value.session.return_value.__enter__ = lambda s: mock_session
        mock_gdb.return_value.session.return_value.__exit__ = MagicMock(
            return_value=False
        )

        with patch("sayou.loader.plugins.neo4j_writer.GraphDatabase", mock_gdb):
            pipeline = LoaderPipeline(extra_writers=[Neo4jWriter])
            data = [{"id": "n1", "label": "Person", "name": "Alice"}]
            result = pipeline.run(
                data,
                "bolt://localhost:7687",
                strategy="Neo4jWriter",
                auth=("neo4j", "password"),
            )
        assert result is True
