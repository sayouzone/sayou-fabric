# ── Setup
"""
Transfer rows from a SQLite database to a local archive using
`TransferPipeline`.

`SqliteGenerator` paginates through any `SELECT` query with `LIMIT` /
`OFFSET`.  `SqliteFetcher` executes each page and returns rows as
`list[dict]`.  SQLite is part of the Python standard library — no mock
is required.

The example below creates an in-memory database for self-contained testing.

```bash
python quick_start_sqlite.py
```
"""
import json
import os
import sqlite3
import tempfile

from sayou.brain.pipelines.transfer import TransferPipeline


def setup_demo_db() -> str:
    """Create a temporary SQLite database with 25 sample rows."""
    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    path = f.name
    f.close()

    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE employees "
        "(id INTEGER PRIMARY KEY, name TEXT, department TEXT, salary REAL)"
    )
    rows = [
        (
            i,
            f"Employee_{i}",
            ["Engineering", "Design", "Marketing"][i % 3],
            70000 + i * 1000,
        )
        for i in range(1, 26)
    ]
    cur.executemany("INSERT INTO employees VALUES (?, ?, ?, ?)", rows)
    conn.commit()
    conn.close()
    return path


DB_PATH = setup_demo_db()
OUTPUT_DIR = "./sayou_archive/sqlite"


# ── Basic Query Transfer
"""
Pass the `.db` file path as `source`.  The `query` keyword accepts any
valid `SELECT` statement (no trailing semicolon).  `batch_size` controls
how many rows are fetched per request (default: 1 000).

Each batch is written as a separate file in `destination`.  Stats:
```python
{"read": <batches_fetched>, "written": <files_written>, "failed": <int>}
```
"""
stats = TransferPipeline.process(
    source=DB_PATH,
    destination=OUTPUT_DIR,
    strategies={"connector": "sqlite"},
    query="SELECT id, name, department, salary FROM employees",
    batch_size=10,
)

print("=== Basic Query Transfer ===")
print(json.dumps(stats, indent=2))


# ── URI Format
"""
`SqliteGenerator` also accepts the standard `sqlite:///` URI prefix used
by SQLAlchemy and other tools.
"""
stats_uri = TransferPipeline.process(
    source=f"sqlite:///{DB_PATH}",
    destination=os.path.join(OUTPUT_DIR, "uri_run"),
    strategies={"connector": "sqlite"},
    query="SELECT * FROM employees ORDER BY salary DESC",
    batch_size=10,
)

print("=== URI Format ===")
print(json.dumps(stats_uri, indent=2))


# ── Filtered Query
"""
Any SQL expression is valid — `WHERE`, `JOIN`, `GROUP BY`.  The generator
stops automatically when a batch returns fewer rows than `batch_size`.
"""
stats_filtered = TransferPipeline.process(
    source=DB_PATH,
    destination=os.path.join(OUTPUT_DIR, "engineering"),
    strategies={"connector": "sqlite"},
    query=(
        "SELECT id, name, salary FROM employees "
        "WHERE department = 'Engineering' "
        "ORDER BY salary DESC"
    ),
    batch_size=10,
)

print("=== Filtered Query ===")
print(json.dumps(stats_filtered, indent=2))


# ── Validate Output
"""
Inspect the archive to confirm all batches were written.
"""
if os.path.isdir(OUTPUT_DIR):
    files = [
        n for n in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, n))
    ]
    print(f"\nArchived {len(files)} batch file(s) in '{OUTPUT_DIR}'.")

os.unlink(DB_PATH)
