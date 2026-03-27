"""
Unit tests for FileWriter and JsonLineWriter.
"""

import json
import os
from unittest.mock import MagicMock, mock_open, patch

import pytest

from sayou.loader.writer.file_writer import FileWriter
from sayou.loader.writer.jsonl_writer import JsonLineWriter

# ---------------------------------------------------------------------------
# FileWriter.can_handle
# ---------------------------------------------------------------------------


class TestFileWriterCanHandle:
    def test_explicit_file_strategy(self):
        assert FileWriter.can_handle([], "out.json", "file") == 1.0

    def test_local_path_without_scheme_scores_high(self):
        assert FileWriter.can_handle([], "/tmp/out", "auto") == 0.9

    def test_jsonl_extension_scores_lower(self):
        score = FileWriter.can_handle([], "out.jsonl", "auto")
        assert score == 0.5

    def test_file_scheme_returns_1(self):
        assert FileWriter.can_handle([], "file:///tmp/out.json", "auto") == 1.0

    def test_empty_destination_returns_zero(self):
        assert FileWriter.can_handle([], "", "auto") == 0.0

    def test_http_scheme_returns_zero(self):
        assert FileWriter.can_handle([], "http://example.com/file", "auto") == 0.0


# ---------------------------------------------------------------------------
# FileWriter._detect_extension
# ---------------------------------------------------------------------------


class TestFileWriterDetectExtension:
    def setup_method(self):
        import logging

        self.writer = FileWriter()
        self.writer.logger = logging.getLogger("test")
        self.writer._callbacks = []

    def test_metadata_extension_takes_priority(self):
        ext = self.writer._detect_extension("anything", {"extension": ".csv"})
        assert ext == ".csv"

    def test_html_sniffed_from_content(self):
        html = "<html><body><p>Hello</p></body></html>"
        ext = self.writer._detect_extension(html, {})
        assert ext == ".html"

    def test_markdown_sniffed_from_content(self):
        md = "# Heading\n\nSome text."
        ext = self.writer._detect_extension(md, {})
        assert ext == ".md"

    def test_json_sniffed_from_dict(self):
        ext = self.writer._detect_extension({"key": "value"}, {})
        assert ext == ".json"

    def test_pdf_magic_bytes(self):
        ext = self.writer._detect_extension(b"%PDF-1.4", {})
        assert ext == ".pdf"

    def test_png_magic_bytes(self):
        ext = self.writer._detect_extension(b"\x89PNG\r\n\x1a\n", {})
        assert ext == ".png"

    def test_jpeg_magic_bytes(self):
        ext = self.writer._detect_extension(b"\xff\xd8\xff", {})
        assert ext == ".jpg"

    def test_plain_text_defaults_to_txt(self):
        ext = self.writer._detect_extension("just plain text", {})
        assert ext == ".txt"


# ---------------------------------------------------------------------------
# FileWriter._do_write
# ---------------------------------------------------------------------------


class TestFileWriterDoWrite:
    def setup_method(self):
        import logging

        self.writer = FileWriter()
        self.writer.logger = logging.getLogger("test")
        self.writer._callbacks = []

    def test_writes_dict_as_json(self, tmp_path):
        dest = str(tmp_path / "out.json")
        result = self.writer._do_write({"key": "value"}, dest)
        assert result is True
        with open(dest) as f:
            data = json.load(f)
        assert data["key"] == "value"

    def test_writes_string(self, tmp_path):
        dest = str(tmp_path / "out.txt")
        result = self.writer._do_write("hello world", dest)
        assert result is True
        assert open(dest).read() == "hello world"

    def test_writes_bytes(self, tmp_path):
        dest = str(tmp_path / "out.bin")
        result = self.writer._do_write(b"\x00\x01\x02", dest)
        assert result is True
        assert open(dest, "rb").read() == b"\x00\x01\x02"

    def test_auto_detects_json_extension(self, tmp_path):
        dest = str(tmp_path / "out")  # no extension
        self.writer._do_write({"a": 1}, dest)
        assert os.path.exists(dest + ".json")

    def test_creates_parent_directories(self, tmp_path):
        dest = str(tmp_path / "nested" / "deep" / "out.json")
        self.writer._do_write({"x": 1}, dest)
        assert os.path.exists(dest)


# ---------------------------------------------------------------------------
# JsonLineWriter
# ---------------------------------------------------------------------------


class TestJsonLineWriter:
    def setup_method(self):
        import logging

        self.writer = JsonLineWriter()
        self.writer.logger = logging.getLogger("test")
        self.writer._callbacks = []

    def test_can_handle_jsonl_strategy(self):
        assert JsonLineWriter.can_handle([], "out.jsonl", "jsonl") == 1.0

    def test_can_handle_jsonl_extension(self):
        assert JsonLineWriter.can_handle([], "data.jsonl", "auto") == 1.0

    def test_non_list_returns_false(self, tmp_path):
        dest = str(tmp_path / "out.jsonl")
        result = self.writer._do_write({"not": "a list"}, dest)
        assert result is False

    def test_writes_one_line_per_item(self, tmp_path):
        dest = str(tmp_path / "out.jsonl")
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        self.writer._do_write(data, dest)
        lines = open(dest).read().strip().splitlines()
        assert len(lines) == 3
        assert json.loads(lines[0])["id"] == 1

    def test_each_line_is_valid_json(self, tmp_path):
        dest = str(tmp_path / "out.jsonl")
        data = [{"k": "v", "n": 42}] * 5
        self.writer._do_write(data, dest)
        for line in open(dest):
            parsed = json.loads(line)
            assert parsed["k"] == "v"
