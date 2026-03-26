!!! abstract "Source"
    Synced from [`packages/sayou-connector/examples/quick_start_postgresql.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-connector/examples/quick_start_postgresql.py).

## Setup

Transfer data from PostgreSQL to a local archive using `TransferPipeline`.

`PostgresqlGenerator` yields one task per table name or one task for a
custom SQL query.  `PostgresqlFetcher` connects via `psycopg2` with
`RealDictCursor`, fetches rows in batches of 5 000, and serialises
`UUID`, `Decimal`, and `datetime` fields automatically.

Install the dependency before running with a real database:

```bash
pip install psycopg2-binary
python quick_start_postgresql.py
```

The example below mocks `psycopg2` so it runs without a PostgreSQL server.
Remove `setup_mock()`, update `connection_args`, and set `tables` to go live.

```python
import datetime
import decimal
import json
import os
import sys
import uuid
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline

OUTPUT_DIR = "./sayou_archive/postgresql"
```

## Mock Setup

`PostgresqlFetcher` calls:
  - `psycopg2.connect(dbname=…, user=…, password=…, host=…, port=…)`
  - `conn.cursor(cursor_factory=RealDictCursor)` — dict-returning cursor
  - `cursor.execute(sql)` → `cursor.fetchmany(5000)`

The mock returns two rows with UUID, Decimal, and datetime fields to
verify `_sanitize_dict()`.

To switch to live mode: delete this function and its call below.

```python
def setup_mock():
    rows_batch_1 = [
        {
            "id": str(uuid.uuid4()),
            "name": "Alice Johnson",
            "department": "Engineering",
            "salary": 95000.00,
            "hired_at": "2022-03-15T09:00:00",
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Bob Smith",
            "department": "Design",
            "salary": 82000.00,
            "hired_at": "2021-07-01T09:00:00",
        },
    ]

    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchmany.side_effect = [rows_batch_1, []]

    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value = mock_cursor

    mock_psycopg2 = MagicMock()
    mock_psycopg2.connect.return_value = mock_conn

    mock_extras = MagicMock()
    mock_psycopg2.extras = mock_extras

    sys.modules["psycopg2"] = mock_psycopg2
    sys.modules["psycopg2.extras"] = mock_extras
```

## Transfer Tables

List table names in `tables`.  `PostgresqlFetcher` issues
`SELECT * FROM {table}` for each entry.

`connection_args` fields:
  - `host`     — PostgreSQL server hostname
  - `port`     — default: 5432
  - `dbname`   — database name
  - `user`     — PostgreSQL role
  - `password` — role password

Both `postgres://` and `postgresql://` source prefixes are supported.

```python
setup_mock()

stats = TransferPipeline.process(
    source="postgresql://localhost:5432/mydb",
    destination=OUTPUT_DIR,
    strategies={"connector": "postgres"},
    tables=["employees", "departments"],
    connection_args={
        "host": "localhost",
        "port": 5432,
        "dbname": "mydb",
        "user": os.environ.get("PG_USER", "postgres"),
        "password": os.environ.get("PG_PASSWORD", "mock-password"),
    },
)

print("=== Transfer Tables ===")
print(json.dumps(stats, indent=2))
```

## Transfer with Custom Query

Use `query` for SQL with joins, CTEs, or window functions.

```python
setup_mock()

stats_query = TransferPipeline.process(
    source="postgresql://localhost:5432/mydb",
    destination=f"{OUTPUT_DIR}/custom",
    strategies={"connector": "postgres"},
    query=(
        "SELECT e.id, e.name, d.name AS dept, e.salary, "
        "       RANK() OVER (PARTITION BY e.department ORDER BY e.salary DESC) AS rank "
        "FROM employees e "
        "JOIN departments d ON e.department_id = d.id "
        "WHERE e.salary > 70000"
    ),
    connection_args={
        "host": "localhost",
        "dbname": "mydb",
        "user": os.environ.get("PG_USER", "postgres"),
        "password": os.environ.get("PG_PASSWORD", "mock-password"),
    },
)

print("=== Transfer with Custom Query ===")
print(json.dumps(stats_query, indent=2))
```

## Validate Output

Each table or query produces one archive file.  All PostgreSQL-specific
types (UUID, Decimal, datetime, date) are serialised to JSON-safe values.

```python
if os.path.isdir(OUTPUT_DIR):
    files = [
        n for n in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, n))
    ]
    print(f"\nArchived {len(files)} file(s) in '{OUTPUT_DIR}'.")
    if files:
        with open(os.path.join(OUTPUT_DIR, files[0]), encoding="utf-8") as f:
            print(f.read(400))
```