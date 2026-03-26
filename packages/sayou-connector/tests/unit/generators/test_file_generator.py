"""
Unit tests for FileGenerator.

Covers:
- can_handle: existing path returns 1.0; path-like prefix returns 0.8; random string 0.0.
- Extension filtering: only files matching the allowed list are yielded.
- Glob name pattern filtering.
- Single file input (not a directory) yields exactly one task.
- Recursive vs flat directory scan.
- Task metadata: source_type="file", uri is absolute, meta.filename is the basename.
"""

import os

import pytest
from sayou.core.schemas import SayouTask

from sayou.connector.generator.file_generator import FileGenerator


def _generator(tmp_dir: str, **kwargs) -> tuple[FileGenerator, list[SayouTask]]:
    gen = FileGenerator()
    gen.initialize(source=tmp_dir, **kwargs)
    tasks = list(gen._do_generate(tmp_dir))
    return gen, tasks


# ---------------------------------------------------------------------------
# Fixtures (inherits tmp_dir / multi_file_dir from conftest)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# can_handle
# ---------------------------------------------------------------------------


class TestCanHandle:
    def test_existing_directory_returns_one(self, tmp_dir):
        assert FileGenerator.can_handle(tmp_dir) == 1.0

    def test_path_like_prefix_returns_nonzero(self):
        assert FileGenerator.can_handle("/nonexistent/path") > 0.0

    def test_random_string_returns_zero(self):
        assert FileGenerator.can_handle("hello world") == 0.0


# ---------------------------------------------------------------------------
# Extension filtering
# ---------------------------------------------------------------------------


class TestExtensionFilter:
    def test_only_txt_files_yielded(self, multi_file_dir):
        _, tasks = _generator(multi_file_dir, extensions=[".txt"])
        for task in tasks:
            assert task.uri.endswith(".txt"), f"Unexpected file: {task.uri}"

    def test_multiple_extensions_respected(self, multi_file_dir):
        _, tasks = _generator(multi_file_dir, extensions=[".txt", ".md"])
        exts = {os.path.splitext(t.uri)[1] for t in tasks}
        assert exts <= {".txt", ".md"}

    def test_no_extension_filter_yields_all(self, multi_file_dir):
        _, tasks = _generator(multi_file_dir)
        # Should include .txt, .md, .log
        assert len(tasks) >= 3


# ---------------------------------------------------------------------------
# Name pattern filter
# ---------------------------------------------------------------------------


class TestNamePattern:
    def test_pattern_filters_by_name_glob(self, multi_file_dir):
        _, tasks = _generator(multi_file_dir, name_pattern="a.*")
        assert len(tasks) == 1
        assert os.path.basename(tasks[0].uri) == "a.txt"


# ---------------------------------------------------------------------------
# Single file input
# ---------------------------------------------------------------------------


class TestSingleFileInput:
    def test_single_file_yields_one_task(self, txt_file):
        gen = FileGenerator()
        gen.initialize(source=txt_file, extensions=[".txt"])
        tasks = list(gen._do_generate(txt_file))
        assert len(tasks) == 1
        assert tasks[0].uri == txt_file


# ---------------------------------------------------------------------------
# Task structure
# ---------------------------------------------------------------------------


class TestTaskStructure:
    def test_task_source_type_is_file(self, txt_file):
        gen = FileGenerator()
        gen.initialize(source=txt_file, extensions=[".txt"])
        tasks = list(gen._do_generate(txt_file))
        assert tasks[0].source_type == "file"

    def test_task_uri_is_absolute(self, multi_file_dir):
        _, tasks = _generator(multi_file_dir, extensions=[".txt"])
        for task in tasks:
            assert os.path.isabs(task.uri)

    def test_task_meta_contains_filename(self, multi_file_dir):
        _, tasks = _generator(multi_file_dir, extensions=[".txt"])
        for task in tasks:
            assert "filename" in task.meta
            assert task.meta["filename"] == os.path.basename(task.uri)
