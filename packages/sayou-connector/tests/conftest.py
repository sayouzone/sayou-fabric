"""
Shared pytest fixtures for the sayou-connector test suite.
"""

import os
import shutil
import sqlite3
import tempfile
from typing import Iterator
from unittest.mock import MagicMock

import pytest
from sayou.core.schemas import SayouPacket, SayouTask

# ---------------------------------------------------------------------------
# Filesystem helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_dir() -> Iterator[str]:
    """Yield a temporary directory that is cleaned up after the test."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def txt_file(tmp_dir: str) -> str:
    """Write a single .txt file and return its path."""
    path = os.path.join(tmp_dir, "sample.txt")
    with open(path, "w") as f:
        f.write("Hello Sayou")
    return path


@pytest.fixture
def multi_file_dir(tmp_dir: str) -> str:
    """Create a directory with multiple files of different extensions."""
    files = {
        "a.txt": "Content A",
        "b.txt": "Content B",
        "c.md": "Content C",
        "ignore.log": "Should be ignored",
    }
    for name, content in files.items():
        with open(os.path.join(tmp_dir, name), "w") as f:
            f.write(content)
    return tmp_dir


# ---------------------------------------------------------------------------
# SQLite helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def sqlite_db(tmp_dir: str) -> str:
    """Create a SQLite DB with 25 rows and return its path."""
    db_path = os.path.join(tmp_dir, "test.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE data (id INTEGER PRIMARY KEY, name TEXT)")
    for i in range(25):
        cur.execute("INSERT INTO data VALUES (?, ?)", (i, f"row_{i}"))
    conn.commit()
    conn.close()
    return db_path


# ---------------------------------------------------------------------------
# SayouTask / SayouPacket factories
# ---------------------------------------------------------------------------


def make_task(
    source_type: str = "file",
    uri: str = "/tmp/test.txt",
    params: dict = None,
    meta: dict = None,
) -> SayouTask:
    return SayouTask(
        source_type=source_type,
        uri=uri,
        params=params or {},
        meta=meta or {},
    )


def make_packet(
    task: SayouTask, data=None, success: bool = True, error: str = None
) -> SayouPacket:
    return SayouPacket(task=task, data=data, success=success, error=error)
