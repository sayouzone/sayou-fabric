!!! abstract "Source"
    Synced from [`packages/sayou-connector/examples/quick_start_mysql.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-connector/examples/quick_start_mysql.py).

## Setup

Transfer data from MySQL (or MariaDB) to a local archive using
`TransferPipeline`.

`MySQLGenerator` yields one task per table name or one task for a custom
query.  `MySQLFetcher` connects via `pymysql` with `DictCursor`, executes
the SQL in batches of 5 000 rows, and serialises `datetime`, `Decimal`,
and `bytes` fields automatically.

Install the dependency before running with a real database:

```bash
pip install pymysql
python quick_start_mysql.py
```

The example below mocks `pymysql` so it runs without a MySQL server.
Remove `setup_mock()`, update `connection_args`, and set `tables` to go live.

```python
import json
import os
import sys
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline

OUTPUT_DIR = "./sayou_archive/mysql"
```

## Mock Setup

`MySQLFetcher` calls `pymysql.connect(host=…, cursorclass=DictCursor)`
then `cursor.execute(sql)` and `cursor.fetchmany(5000)`.

The mock returns two rows to verify basic collection flow.

To switch to live mode: delete this function and its call below.

```python
def setup_mock():
    rows_batch_1 = [
        {"id": 1, "username": "alice", "email": "alice@example.com", "active": True},
        {"id": 2, "username": "bob", "email": "bob@example.com", "active": False},
    ]

    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchmany.side_effect = [rows_batch_1, []]

    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value = mock_cursor

    mock_pymysql = MagicMock()
    mock_pymysql.connect.return_value = mock_conn
    mock_pymysql.cursors = MagicMock()
    mock_pymysql.cursors.DictCursor = MagicMock()
    sys.modules["pymysql"] = mock_pymysql
    sys.modules["pymysql.cursors"] = mock_pymysql.cursors
```

## Transfer Tables

List tables in `tables` — `MySQLFetcher` issues `SELECT * FROM {table}`
for each entry.

`connection_args` fields:
  - `host`     — MySQL hostname (default: `"localhost"`)
  - `port`     — default: 3306
  - `user`     — MySQL user
  - `password` — MySQL password
  - `database` — target database name
  - `charset`  — character set (default: `"utf8mb4"`)

Both `mysql://` and `mariadb://` prefixes are auto-detected by the generator.

```python
setup_mock()

stats = TransferPipeline.process(
    source="mysql://localhost:3306/mydb",
    destination=OUTPUT_DIR,
    strategies={"connector": "mysql"},
    tables=["users", "orders"],
    connection_args={
        "host": "localhost",
        "port": 3306,
        "user": os.environ.get("MYSQL_USER", "root"),
        "password": os.environ.get("MYSQL_PASSWORD", "mock-password"),
        "database": "mydb",
        "charset": "utf8mb4",
    },
)

print("=== Transfer Tables ===")
print(json.dumps(stats, indent=2))
```

## Transfer with Custom Query

Use `query` for joins, filters, or aggregations.  The result is written to
a single archive file named `custom_query`.

```python
setup_mock()

stats_query = TransferPipeline.process(
    source="mysql://localhost:3306/mydb",
    destination=f"{OUTPUT_DIR}/custom",
    strategies={"connector": "mysql"},
    query=(
        "SELECT u.id, u.username, COUNT(o.id) AS order_count "
        "FROM users u "
        "LEFT JOIN orders o ON u.id = o.user_id "
        "GROUP BY u.id, u.username "
        "ORDER BY order_count DESC "
        "LIMIT 100"
    ),
    connection_args={
        "host": "localhost",
        "user": os.environ.get("MYSQL_USER", "root"),
        "password": os.environ.get("MYSQL_PASSWORD", "mock-password"),
        "database": "mydb",
    },
)

print("=== Transfer with Custom Query ===")
print(json.dumps(stats_query, indent=2))
```

## Validate Output

Each table or query produces one archive file.

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