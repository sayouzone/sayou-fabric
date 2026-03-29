!!! abstract "Source"
    Synced from [`packages/sayou-loader/examples/quick_start_mongodb.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-loader/examples/quick_start_mongodb.py).

## Setup

Write records to MongoDB using `LoaderPipeline` with `MongoDBWriter`.

`MongoDBWriter` uses ``bulk_write`` with ``UpdateOne(upsert=True)`` for
efficient batch processing.  Documents matching the upsert key are updated
in place; new documents are inserted.  This makes re-running the pipeline
on updated data safe.

URI pattern: ``mongodb://<host>:<port>/<db>/<collection>``

Install:

    pip install pymongo

```python
import logging
from unittest.mock import MagicMock, patch

from sayou.loader.pipeline import LoaderPipeline
from sayou.loader.plugins.mongodb_writer import MongoDBWriter

pipeline = LoaderPipeline(extra_writers=[MongoDBWriter])

RECORDS = [
    {
        "id": "lib-001",
        "name": "Connector",
        "version": "0.1.0",
        "tags": ["collection", "fetch"],
    },
    {"id": "lib-002", "name": "Document", "version": "0.1.0", "tags": ["parse", "pdf"]},
    {
        "id": "lib-003",
        "name": "Refinery",
        "version": "0.1.0",
        "tags": ["normalise", "clean"],
    },
]
```

## Write to MongoDB

Pass the URI as ``mongodb://<host>/<db>/<collection>`` or specify
``collection`` in kwargs.

```python
mock_client = MagicMock()
mock_db = MagicMock()
mock_col = MagicMock()
mock_result = MagicMock(
    matched_count=2, modified_count=2, upserted_count=1, inserted_count=0
)
mock_client.get_default_database.return_value = mock_db
mock_db.__getitem__.return_value = mock_col
mock_col.bulk_write.return_value = mock_result

with patch("sayou.loader.plugins.mongodb_writer.pymongo") as mock_pymongo:
    mock_pymongo.MongoClient.return_value = mock_client
    mock_pymongo.UpdateOne = MagicMock(side_effect=lambda **k: MagicMock())

    result = pipeline.run(
        RECORDS,
        "mongodb://localhost:27017",
        strategy="MongoDBWriter",
        collection="libraries",
        id_key="id",
    )

print("=== Write to MongoDB ===")
print(f"  Result       : {result}")
print(f"  bulk_write   : {mock_col.bulk_write.called}")
print(f"  Matched      : {mock_result.matched_count}")
print(f"  Modified     : {mock_result.modified_count}")
print(f"  Upserted     : {mock_result.upserted_count}")
```

## Upsert Behaviour

Each record is wrapped in ``UpdateOne(filter={id_key: value}, update={"$set": doc}, upsert=True)``.

- Existing document (matching ``id_key``) → updated.
- New document (no match) → inserted.
- Documents without ``id_key`` fall back to ``InsertOne``.

```python
print("\n=== Upsert Behaviour ===")
print("  id present  → UpdateOne(upsert=True)  — update if exists, insert if not")
print("  id absent   → InsertOne               — always insert, no dedup")
```

## SayouNode Normalisation

`MongoDBWriter` maps ``node_id`` → ``id`` for `SayouNode` objects so the
upsert key resolves correctly.

```python
from sayou.core.schemas import SayouNode

mw = MongoDBWriter()
mw.logger = logging.getLogger("test")
mw._callbacks = []

node = SayouNode(
    node_id="my-node",
    node_class="Topic",
    attributes={"schema:text": "Architecture overview"},
)
norm = mw._normalize_input_data([node])

print("\n=== SayouNode Normalisation ===")
print(f"  id          : {norm[0].get('id')}")
print(f"  schema:text : {norm[0].get('schema:text')!r}")
```

## URI Parsing

URI components are parsed automatically from the ``mongodb://`` URI.
You can also pass ``collection`` and ``dbname`` as kwargs to override.

```python
print("\n=== can_handle Routing ===")
cases = [
    ("mongodb://localhost:27017/db/col", "auto", True),
    ("mongodb://localhost", "mongodb", True),
    ("postgresql://host/db", "auto", False),
]
for uri, strat, expected in cases:
    score = MongoDBWriter.can_handle([], uri, strat)
    matched = bool(score)
    status = "✓" if matched == expected else "✗"
    print(f"  {status} strategy={strat:10s} uri={uri:38s} → {score}")
```

## Real Connection

pipeline.run(
    records,
    "mongodb://user:pass@host:27017/sayou_db/libraries",
    strategy="MongoDBWriter",
    id_key="id",
)

# With explicit kwargs instead of URI
pipeline.run(
    records,
    "mongodb://localhost:27017/",
    strategy="MongoDBWriter",
    collection="libraries",
    dbname="sayou_db",
    id_key="id",
)