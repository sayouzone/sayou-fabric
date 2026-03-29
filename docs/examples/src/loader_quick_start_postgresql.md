!!! abstract "Source"
    Synced from [`packages/sayou-loader/examples/quick_start_postgresql.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-loader/examples/quick_start_postgresql.py).

## Setup

Persist records to PostgreSQL using `LoaderPipeline` with
`PostgresWriter`.

`PostgresWriter` generates a dynamic ``INSERT … ON CONFLICT DO UPDATE``
(UPSERT) statement inferred from the first row's keys.

Features:
- Primary key(s) configurable via ``pk_columns`` (default ``["id"]``)
- ``dict`` and ``list`` column values are automatically JSON-serialised
- Re-running on updated data updates existing rows, never duplicates

URI pattern: ``postgresql://user:password@host:5432/database``

Install:

    pip install psycopg2-binary

```python
import json
import logging
from unittest.mock import MagicMock, patch

from sayou.loader.pipeline import LoaderPipeline
from sayou.loader.plugins.postgres_writer import PostgresWriter

pipeline = LoaderPipeline(extra_writers=[PostgresWriter])

RECORDS = [
    {
        "id": "lib-001",
        "name": "Connector",
        "version": "0.1.0",
        "stable": True,
        "tags": ["collection", "fetch"],
    },
    {
        "id": "lib-002",
        "name": "Document",
        "version": "0.1.0",
        "stable": True,
        "tags": ["parse", "pdf", "docx"],
    },
    {
        "id": "lib-003",
        "name": "Refinery",
        "version": "0.1.0",
        "stable": True,
        "tags": ["normalise", "clean"],
    },
]
```

## Write to PostgreSQL

The writer:
1. Infers column names from the first row's keys.
2. Builds a parametrised ``INSERT … ON CONFLICT DO UPDATE`` statement.
3. Serialises ``dict`` / ``list`` values to JSON strings.
4. Executes all rows in a single ``executemany()`` call.

```python
mock_conn = MagicMock()
mock_cursor = MagicMock()
mock_conn.cursor.return_value = mock_cursor

with patch("sayou.loader.plugins.postgres_writer.psycopg2") as mock_pg:
    mock_pg.connect.return_value = mock_conn

    result = pipeline.run(
        RECORDS,
        "postgresql://user:pass@localhost:5432/sayou_db",
        strategy="PostgresWriter",
        table_name="libraries",
        pk_columns=["id"],
    )

print("=== Write to PostgreSQL ===")
print(f"  Result          : {result}")
print(f"  executemany     : {mock_cursor.executemany.called}")
print(f"  commit          : {mock_conn.commit.called}")

if mock_cursor.executemany.called:
    sql = mock_cursor.executemany.call_args[0][0].strip()
    print(f"\n  Generated SQL (trimmed):")
    for line in sql.splitlines():
        print(f"    {line}")
```

## JSON Serialisation of Complex Columns

PostgreSQL ``jsonb`` or ``text`` columns can store JSON.
``dict`` and ``list`` values are auto-converted before insertion.

```python
pw = PostgresWriter()
pw.logger = logging.getLogger("test")
pw._callbacks = []
norm = pw._normalize_input_data(RECORDS)

print("\n=== JSON Serialisation Preview ===")
row = norm[0]
for col, val in row.items():
    if isinstance(val, list):
        print(f"  {col:10s}: {json.dumps(val)!r}  ← will be JSON string")
    else:
        print(f"  {col:10s}: {val!r}")
```

## Composite Primary Key

Pass a list to ``pk_columns`` to build a composite conflict clause:

    ON CONFLICT (tenant_id, record_id) DO UPDATE SET …

```python
print("\n=== Composite Primary Key ===")
print("  pk_columns=['id']                → ON CONFLICT (id)")
print("  pk_columns=['tenant_id', 'id']   → ON CONFLICT (tenant_id, id)")
```

## can_handle Routing

Matches ``postgres://``, ``postgresql://`` URIs and the explicit
``"postgres"`` / ``"postgresql"`` strategy keys.

```python
print("\n=== can_handle Routing ===")
cases = [
    ("postgresql://host/db", "auto", True),
    ("postgres://host/db", "auto", True),
    ("postgresql://host/db", "postgres", True),
    ("neo4j://host", "auto", False),
]
for uri, strat, expected in cases:
    score = PostgresWriter.can_handle([], uri, strat)
    status = "✓" if bool(score) == expected else "✗"
    print(f"  {status} strategy={strat:12s} uri={uri:28s} → {score}")
```

## SayouNode Normalisation

`PostgresWriter` extracts ``.attributes`` from `SayouNode` objects and
treats them as the row dict.

```python
from sayou.core.schemas import SayouNode

node = SayouNode(
    node_id="n1", node_class="Topic", attributes={"id": "n1", "name": "Arch", "page": 1}
)
norm_node = pw._normalize_input_data([node])

print("\n=== SayouNode Normalisation ===")
print(f"  Row keys: {list(norm_node[0].keys())}")
```

## Real Connection

pipeline.run(
    records,
    "postgresql://user:pass@host:5432/sayou_db",
    strategy="PostgresWriter",
    table_name="libraries",
    pk_columns=["id"],
)

# Connection args dict instead of URI
pipeline.run(
    records,
    "raw_table_name",                          # used as table fallback
    strategy="PostgresWriter",
    table_name="libraries",
    connection_args={
        "host": "localhost", "port": 5432,
        "user": "admin",    "password": "secret",
        "dbname": "sayou_db",
    },
)