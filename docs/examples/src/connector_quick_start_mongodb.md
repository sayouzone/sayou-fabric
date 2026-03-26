!!! abstract "Source"
    Synced from [`packages/sayou-connector/examples/quick_start_mongodb.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-connector/examples/quick_start_mongodb.py).

## Setup

Transfer documents from a MongoDB collection to a local archive using
`TransferPipeline`.

`MongoDBGenerator` yields one task per collection name.
`MongoDBFetcher` executes a `find()` query and returns all matching
documents as a list of dicts, with `ObjectId` and `datetime` fields
automatically serialised to strings.

Install the dependency before running with a real database:

```bash
pip install pymongo
python quick_start_mongodb.py
```

The example below mocks `pymongo` so it runs without a MongoDB instance.
Remove `setup_mock()`, update `connection_args`, and set `collections` to
go live.

```python
import datetime
import json
import os
import sys
import uuid
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline

OUTPUT_DIR = "./sayou_archive/mongodb"
```

## Mock Setup

`MongoDBFetcher` calls:
  - `pymongo.MongoClient(uri)` — connect
  - `client[db_name][collection].find(filter).limit(n)` — query

The mock returns three sample documents from the `products` collection.
`ObjectId` and `datetime` fields are included to verify that the fetcher's
`_sanitize()` method converts them correctly.

To switch to live mode: delete this function and its call below.

```python
def setup_mock():
    mock_doc_1 = {
        "_id": "507f1f77bcf86cd799439011",  # pre-stringified for simplicity
        "name": "Sayou Fabric Pro",
        "price": 99.99,
        "created_at": "2024-01-01T00:00:00",
        "tags": ["data", "pipeline", "llm"],
        "in_stock": True,
    }
    mock_doc_2 = {
        "_id": "507f1f77bcf86cd799439012",
        "name": "Sayou Brain Lite",
        "price": 49.99,
        "created_at": "2024-02-15T10:30:00",
        "tags": ["ai", "orchestration"],
        "in_stock": False,
    }
    mock_doc_3 = {
        "_id": "507f1f77bcf86cd799439013",
        "name": "Sayou Connector Pack",
        "price": 29.99,
        "created_at": "2024-03-01T08:00:00",
        "tags": ["connector", "integration"],
        "in_stock": True,
    }

    mock_cursor = MagicMock()
    mock_cursor.__iter__ = MagicMock(
        return_value=iter([mock_doc_1, mock_doc_2, mock_doc_3])
    )

    mock_collection = MagicMock()
    mock_collection.find.return_value.limit.return_value = mock_cursor

    mock_db = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    mock_client = MagicMock()
    mock_client.__getitem__.return_value = mock_db
    mock_client.get_default_database.return_value = mock_db

    mock_pymongo = MagicMock()
    mock_pymongo.MongoClient.return_value = mock_client

    # bson.ObjectId stub
    mock_bson = MagicMock()
    sys.modules["pymongo"] = mock_pymongo
    sys.modules["bson"] = mock_bson
```

## Transfer a Collection

Pass a MongoDB connection URI as `source`.  List the target collection
names in `collections` — one task is created per collection.

`connection_args` accepts:
  - `uri`      — full connection string (recommended)
  - `host`, `port`, `user`, `password`, `dbname` — individual fields

`query` is an optional `find()` filter dict (default: `{}` — all docs).

```python
setup_mock()

stats = TransferPipeline.process(
    source="mongodb://localhost:27017/mydb",
    destination=OUTPUT_DIR,
    strategies={"connector": "mongodb"},
    collections=["products"],
    connection_args={
        "uri": "mongodb://localhost:27017/",
        "dbname": "mydb",
    },
)

print("=== Transfer a Collection ===")
print(json.dumps(stats, indent=2))
```

## Transfer Multiple Collections with a Filter

Pass multiple collection names to transfer them in a single pipeline run.
Use `query` to apply a `find()` filter to every collection.

```python
setup_mock()

stats_multi = TransferPipeline.process(
    source="mongodb://localhost:27017/mydb",
    destination=f"{OUTPUT_DIR}/filtered",
    strategies={"connector": "mongodb"},
    collections=["products", "orders", "users"],
    connection_args={
        "uri": "mongodb://localhost:27017/",
        "dbname": "mydb",
    },
    query={"in_stock": True},
)

print("=== Transfer Multiple Collections with a Filter ===")
print(json.dumps(stats_multi, indent=2))
```

## Validate Output

Each collection produces one archive file.  The documents are serialised
as JSON with all ObjectId and datetime fields converted to strings.

```python
if os.path.isdir(OUTPUT_DIR):
    files = [
        n for n in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, n))
    ]
    print(f"\nArchived {len(files)} collection file(s) in '{OUTPUT_DIR}'.")
    if files:
        with open(os.path.join(OUTPUT_DIR, files[0]), encoding="utf-8") as f:
            print(f.read(400))
```