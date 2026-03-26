!!! abstract "Source"
    Synced from [`packages/sayou-connector/examples/quick_start_mssql.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-connector/examples/quick_start_mssql.py).

## Setup

Transfer data from Microsoft SQL Server to a local archive using
`TransferPipeline`.

`MSSQLGenerator` yields one task per table name or one task for a custom
query.  `MSSQLFetcher` connects via `pymssql`, executes the SQL, and
returns all rows as `list[dict]` with `datetime`, `Decimal`, and `UUID`
fields automatically serialised.

Install the dependency before running with a real server:

```bash
pip install pymssql
python quick_start_mssql.py
```

The example below mocks `pymssql` so it runs without a SQL Server instance.
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

OUTPUT_DIR = "./sayou_archive/mssql"
```

## Mock Setup

`MSSQLFetcher` calls `pymssql.connect(server=…, user=…, password=…,
database=…, as_dict=True)` then `cursor.execute(sql)` and
`cursor.fetchmany(5000)`.

The mock returns two rows with date, decimal, and UUID fields to verify
the fetcher's `_sanitize_mssql_types()` method.

To switch to live mode: delete this function and its call below.

```python
def setup_mock():
    rows_batch_1 = [
        {
            "id": str(uuid.uuid4()),
            "name": "Product A",
            "price": 99.99,
            "created_at": "2024-01-01T00:00:00",
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Product B",
            "price": 49.99,
            "created_at": "2024-02-15T10:30:00",
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

    mock_pymssql = MagicMock()
    mock_pymssql.connect.return_value = mock_conn
    sys.modules["pymssql"] = mock_pymssql
```

## Transfer Tables

List tables in `tables` — one task is created per table name.
`MSSQLFetcher` issues `SELECT * FROM {table}` for each entry.

`connection_args` fields:
  - `host` (or `server`) — SQL Server hostname or IP
  - `port`               — default: 1433
  - `user`               — SQL login
  - `password`           — SQL password
  - `database`           — target database name

```python
setup_mock()

stats = TransferPipeline.process(
    source="mssql://localhost:1433/mydb",
    destination=OUTPUT_DIR,
    strategies={"connector": "mssql"},
    tables=["products", "orders"],
    connection_args={
        "host": "localhost",
        "port": 1433,
        "user": os.environ.get("MSSQL_USER", "sa"),
        "password": os.environ.get("MSSQL_PASSWORD", "mock-password"),
        "database": "mydb",
    },
)

print("=== Transfer Tables ===")
print(json.dumps(stats, indent=2))
```

## Transfer with Custom Query

Use `query` instead of `tables` to run any SQL expression.  The entire
result set is written to a single archive file.

```python
setup_mock()

stats_query = TransferPipeline.process(
    source="mssql://localhost:1433/mydb",
    destination=f"{OUTPUT_DIR}/custom",
    strategies={"connector": "mssql"},
    query=(
        "SELECT p.id, p.name, p.price, c.name AS category "
        "FROM products p "
        "JOIN categories c ON p.category_id = c.id "
        "WHERE p.price > 10 "
        "ORDER BY p.price DESC"
    ),
    connection_args={
        "host": "localhost",
        "user": os.environ.get("MSSQL_USER", "sa"),
        "password": os.environ.get("MSSQL_PASSWORD", "mock-password"),
        "database": "mydb",
    },
)

print("=== Transfer with Custom Query ===")
print(json.dumps(stats_query, indent=2))
```

## Validate Output

Each table or query produces one archive file.  All SQL Server-specific
types (datetime, decimal, UUID) are serialised to standard JSON.

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