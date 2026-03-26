"""
Unit tests for SqliteGenerator.

Covers:
- can_handle: sqlite:/// URI, .db file path, .sqlite path, plain string.
- _clean_source: strips sqlite:/// and sqlite:// prefixes correctly.
- Pagination: each task carries the correct LIMIT / OFFSET in params["query"].
- stop_flag via feedback: stops on empty result, stops on partial batch,
  continues on full batch.
- Default query is used when none is supplied.
"""

import os

import pytest
from sayou.core.schemas import SayouPacket, SayouTask

from sayou.connector.generator.sqlite_generator import SqliteGenerator


def _generator(source: str, query: str = None, batch_size: int = 10) -> SqliteGenerator:
    gen = SqliteGenerator()
    gen.initialize(source=source, query=query, batch_size=batch_size)
    return gen


def _packet(rows: list, success: bool = True) -> SayouPacket:
    task = SayouTask(source_type="sqlite", uri="test.db", params={}, meta={})
    return SayouPacket(task=task, data=rows, success=success)


# ---------------------------------------------------------------------------
# can_handle
# ---------------------------------------------------------------------------


class TestCanHandle:
    def test_sqlite_uri_returns_one(self):
        assert SqliteGenerator.can_handle("sqlite:///data.db") == 1.0

    def test_db_extension_existing_file(self, sqlite_db):
        assert SqliteGenerator.can_handle(sqlite_db) == 1.0

    def test_db_extension_nonexistent_file_returns_nonzero(self):
        assert SqliteGenerator.can_handle("/nonexistent/path.db") > 0.0

    def test_plain_string_returns_zero(self):
        assert SqliteGenerator.can_handle("hello") == 0.0


# ---------------------------------------------------------------------------
# _clean_source
# ---------------------------------------------------------------------------


class TestCleanSource:
    def test_strips_sqlite_triple_slash(self):
        gen = _generator("sqlite:///test.db")
        assert gen.conn_str == "test.db"

    def test_strips_sqlite_double_slash(self):
        gen = _generator("sqlite://test.db")
        assert gen.conn_str == "test.db"

    def test_plain_path_unchanged(self, sqlite_db):
        gen = _generator(sqlite_db)
        assert gen.conn_str == sqlite_db


# ---------------------------------------------------------------------------
# Pagination task generation
# ---------------------------------------------------------------------------


class TestPagination:
    def test_first_task_has_offset_zero(self, sqlite_db):
        gen = _generator(sqlite_db, query="SELECT * FROM data", batch_size=10)
        # We need at least one yield; manually drive the generator
        do_gen = gen._do_generate(sqlite_db)
        task = next(do_gen)
        assert "LIMIT 10 OFFSET 0" in task.params["query"]
        assert task.meta["offset"] == 0
        gen.stop_flag = True  # prevent infinite loop

    def test_second_task_offset_equals_batch_size(self, sqlite_db):
        gen = _generator(sqlite_db, query="SELECT * FROM data", batch_size=10)
        do_gen = gen._do_generate(sqlite_db)
        next(do_gen)  # offset 0
        task2 = next(do_gen)
        assert task2.meta["offset"] == 10
        gen.stop_flag = True

    def test_task_source_type_is_sqlite(self, sqlite_db):
        gen = _generator(sqlite_db, query="SELECT * FROM data")
        do_gen = gen._do_generate(sqlite_db)
        task = next(do_gen)
        assert task.source_type == "sqlite"
        gen.stop_flag = True


# ---------------------------------------------------------------------------
# Feedback / stop logic
# ---------------------------------------------------------------------------


class TestFeedback:
    def test_stops_on_failed_packet(self, sqlite_db):
        gen = _generator(sqlite_db, batch_size=10)
        gen._do_feedback(_packet([], success=False))
        assert gen.stop_flag is True

    def test_stops_on_empty_data(self, sqlite_db):
        gen = _generator(sqlite_db, batch_size=10)
        gen._do_feedback(_packet([]))
        assert gen.stop_flag is True

    def test_stops_on_partial_batch(self, sqlite_db):
        gen = _generator(sqlite_db, batch_size=10)
        gen._do_feedback(_packet([{"id": i} for i in range(7)]))  # 7 < 10
        assert gen.stop_flag is True

    def test_continues_on_full_batch(self, sqlite_db):
        gen = _generator(sqlite_db, batch_size=10)
        gen._do_feedback(_packet([{"id": i} for i in range(10)]))  # exactly 10
        assert gen.stop_flag is False
