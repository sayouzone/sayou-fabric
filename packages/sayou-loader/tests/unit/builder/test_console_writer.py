"""
Unit tests for ConsoleWriter.
"""

import json
from unittest.mock import patch

import pytest

from sayou.loader.writer.console_writer import ConsoleWriter


class TestCanHandle:
    def test_console_strategy(self):
        assert ConsoleWriter.can_handle([], "stdout", "console") == 1.0

    def test_stdout_destination(self):
        assert ConsoleWriter.can_handle([], "stdout", "auto") == 1.0

    def test_print_destination(self):
        assert ConsoleWriter.can_handle([], "print", "auto") == 1.0

    def test_unknown_destination_returns_zero(self):
        assert ConsoleWriter.can_handle([], "s3://bucket/file", "auto") == 0.0


class TestDoWrite:
    def setup_method(self):
        import logging

        self.writer = ConsoleWriter()
        self.writer.logger = logging.getLogger("test")
        self.writer._callbacks = []

    def test_returns_true_for_dict(self, capsys):
        result = self.writer._do_write({"key": "val"}, "stdout")
        assert result is True
        out = capsys.readouterr().out
        assert "key" in out

    def test_returns_true_for_list(self, capsys):
        result = self.writer._do_write([1, 2, 3], "stdout")
        assert result is True

    def test_prints_json_for_dict(self, capsys):
        self.writer._do_write({"name": "Alice"}, "stdout")
        out = capsys.readouterr().out
        assert '"name"' in out
        assert '"Alice"' in out

    def test_prints_string_directly(self, capsys):
        self.writer._do_write("plain text", "stdout")
        out = capsys.readouterr().out
        assert "plain text" in out
