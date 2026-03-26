!!! abstract "Source"
    Synced from [`packages/sayou-connector/examples/quick_start_oracle.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-connector/examples/quick_start_oracle.py).

## Setup

Transfer data from Oracle Database to a local archive using
`TransferPipeline`.

`OracleGenerator` yields one task per table name or one task for a custom
SQL query.  `OracleFetcher` connects via `oracledb` (the official Oracle
thin client), executes the statement in batches of 5 000 rows, and
serialises `datetime` and LOB fields automatically.

Install the dependency before running with a real database:

```bash
pip install oracledb
python quick_start_oracle.py
```

The example below mocks `oracledb` so it runs without an Oracle instance.
Remove `setup_mock()`, update `connection_args`, and set `tables` to go live.

```python
import json
import os
import sys
from unittest.mock import MagicMock, patch

from sayou.brain.pipelines.transfer import TransferPipeline

OUTPUT_DIR = "./sayou_archive/oracle"
```

## Mock Setup

`OracleFetcher` calls:
  - `oracledb.connect(user=…, password=…, dsn=…)` — connect
  - `connection.cursor()` — create cursor
  - `cursor.execute(sql)` — run query
  - `cursor.description` — column metadata
  - `cursor.fetchmany(5000)` — batch fetch

The mock simulates two rows from an `EMPLOYEES` table.
`oracledb.CLOB` and `oracledb.BLOB` constants are included so the
`_output_type_handler` callback can be set without error.

To switch to live mode: delete this function and its call below.

```python
def setup_mock():
    rows_batch_1 = [
        ("E001", "Alice Johnson", "Engineering", 95000.00, "2022-03-15"),
        ("E002", "Bob Smith", "Design", 82000.00, "2021-07-01"),
    ]

    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.description = [
        ("EMP_ID",),
        ("NAME",),
        ("DEPARTMENT",),
        ("SALARY",),
        ("HIRE_DATE",),
    ]
    mock_cursor.fetchmany.side_effect = [rows_batch_1, []]

    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value = mock_cursor

    mock_oracledb = MagicMock()
    mock_oracledb.connect.return_value = mock_conn
    mock_oracledb.CLOB = "CLOB_TYPE"
    mock_oracledb.BLOB = "BLOB_TYPE"
    mock_oracledb.DB_TYPE_LONG = "DB_TYPE_LONG"
    mock_oracledb.DB_TYPE_RAW = "DB_TYPE_RAW"
    sys.modules["oracledb"] = mock_oracledb
```

## Transfer Tables

List table names in `tables` — `OracleFetcher` issues `SELECT * FROM {table}`
for each entry.

`connection_args` fields:
  - `dsn`          — full DSN string (preferred): `host:port/service_name`
  - `host`, `port`, `service_name` — used when `dsn` is omitted
  - `user`         — Oracle username
  - `password`     — Oracle password

Both `oracle://` and `oracle+…` prefixes are auto-detected by the generator.

```python
setup_mock()

stats = TransferPipeline.process(
    source="oracle://localhost:1521/ORCL",
    destination=OUTPUT_DIR,
    strategies={"connector": "oracle"},
    tables=["EMPLOYEES", "DEPARTMENTS"],
    connection_args={
        "dsn": "localhost:1521/ORCL",
        "user": os.environ.get("ORACLE_USER", "system"),
        "password": os.environ.get("ORACLE_PASSWORD", "mock-password"),
    },
)

print("=== Transfer Tables ===")
print(json.dumps(stats, indent=2))
```

## Transfer with Custom Query

Use `query` for complex SQL — joins, window functions, CTEs.  The full
result set is written to a single archive file named `custom_query`.

```python
setup_mock()

stats_query = TransferPipeline.process(
    source="oracle://localhost:1521/ORCL",
    destination=f"{OUTPUT_DIR}/custom",
    strategies={"connector": "oracle"},
    query=(
        "SELECT e.emp_id, e.name, d.dept_name, e.salary "
        "FROM EMPLOYEES e "
        "JOIN DEPARTMENTS d ON e.dept_id = d.dept_id "
        "WHERE e.salary > 80000 "
        "ORDER BY e.salary DESC"
    ),
    connection_args={
        "dsn": "localhost:1521/ORCL",
        "user": os.environ.get("ORACLE_USER", "system"),
        "password": os.environ.get("ORACLE_PASSWORD", "mock-password"),
    },
)

print("=== Transfer with Custom Query ===")
print(json.dumps(stats_query, indent=2))
```

## Validate Output

Each table or query produces one archive file.  Oracle-specific types
(LOBs, CLOB) are fetched as text; datetime values are ISO 8601 strings.

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