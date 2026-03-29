!!! abstract "Source"
    Synced from [`packages/sayou-loader/examples/quick_start_elasticsearch.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-loader/examples/quick_start_elasticsearch.py).

## Setup

Index documents into Elasticsearch using `LoaderPipeline` with
`ElasticsearchWriter`.

`ElasticsearchWriter` uses the **Bulk API** for high-throughput indexing.
Documents are upserted by ``_id`` (configurable via ``id_key``) so
re-running the same pipeline on updated data is safe.

URI pattern: ``http://<host>:<port>/<index_name>``

Install:

    pip install elasticsearch

```python
import logging
from unittest.mock import MagicMock, patch

from sayou.loader.pipeline import LoaderPipeline
from sayou.loader.plugins.elasticsearch_writer import ElasticsearchWriter

pipeline = LoaderPipeline(extra_writers=[ElasticsearchWriter])

DOCS = [
    {
        "id": "sayou:doc:guide:c001",
        "text": "Sayou Fabric is a modular LLM data pipeline.",
        "source": "guide.pdf",
        "page": 1,
        "node_class": "sayou:Text",
    },
    {
        "id": "sayou:doc:guide:c002",
        "text": "Connector fetches data from 27 external sources.",
        "source": "guide.pdf",
        "page": 2,
        "node_class": "sayou:Text",
    },
    {
        "id": "sayou:doc:guide:c003",
        "text": "Chunking splits documents into retrieval-ready pieces.",
        "source": "guide.pdf",
        "page": 3,
        "node_class": "sayou:Text",
    },
]
```

## Write to Elasticsearch

Pass the URI as ``http://<host>:<port>/<index_name>``.
The writer splits it into ``hosts`` and ``index_name`` automatically.

Authentication options:

    auth=("user", "password")   # basic auth
    auth="<api_key>"            # API key

```python
mock_es = MagicMock()
mock_es.ping.return_value = True

with patch(
    "sayou.loader.plugins.elasticsearch_writer.Elasticsearch", return_value=mock_es
), patch("sayou.loader.plugins.elasticsearch_writer.helpers") as mock_helpers:

    mock_helpers.bulk.return_value = (len(DOCS), 0)

    result = pipeline.run(
        DOCS,
        "http://localhost:9200/sayou_index",
        strategy="ElasticsearchWriter",
        id_key="id",
    )

print("=== Write to Elasticsearch ===")
print(f"  Result         : {result}")
print(f"  bulk() called  : {mock_helpers.bulk.called}")
success, failed = mock_helpers.bulk.return_value
print(f"  Indexed        : {success}  Failed: {failed}")
```

## Bulk Action Format

Each document is converted to an Elasticsearch bulk action:

    {"_index": "sayou_index", "_id": "<id>", "_source": { … }}

Documents without the ``id_key`` field still produce an action but
without ``_id`` (Elasticsearch auto-assigns an ID).

```python
ew = ElasticsearchWriter()
ew.logger = logging.getLogger("test")
ew._callbacks = []

actions = list(ew._generate_bulk_actions(DOCS, "sayou_index", "id"))

print("\n=== Bulk Action Format ===")
for a in actions:
    print(f"  _id={a['_id']:35s}  _index={a['_index']}")
```

## SayouNode Normalisation

`ElasticsearchWriter` accepts both plain dicts and `SayouNode` objects.
For SayouNode, `attributes` and `metadata` are merged, and `node_id` is
mapped to `node_id` in the document.

```python
from sayou.core.schemas import SayouNode

node = SayouNode(
    node_id="n1",
    node_class="sayou:Text",
    attributes={"schema:text": "hello", "source": "guide.pdf"},
)
normalised = ew._normalize_input_data([node])

print("\n=== SayouNode Normalisation ===")
print(f"  node_id present : {'node_id' in normalised[0]}")
print(f"  schema:text     : {normalised[0].get('schema:text')!r}")
```

## can_handle Routing

The writer auto-detects Elasticsearch destinations by URI scheme or
explicit strategy.

```python
print("\n=== can_handle Routing ===")
cases = [
    ("elasticsearch://host/idx", "auto", True),
    ("http://host:9200/idx", "auto", False),  # no ES scheme
    ("http://host:9200/idx", "elasticsearch", True),  # explicit strategy
    ("s3://bucket/path", "auto", False),
]
for uri, strat, expected in cases:
    score = ElasticsearchWriter.can_handle([], uri, strat)
    matched = bool(score)
    status = "✓" if matched == expected else "✗"
    print(f"  {status} strategy={strat:15s} uri={uri[:30]:30s} → {score}")
```

## Real Connection

pipeline.run(
    docs,
    "http://localhost:9200/sayou_index",
    strategy="ElasticsearchWriter",
    id_key="id",
    auth=("elastic", "changeme"),    # basic auth
    verify_certs=False,              # dev only
)

# Elastic Cloud (API key)
pipeline.run(
    docs,
    "https://my-cluster.es.io:9243/sayou_index",
    strategy="ElasticsearchWriter",
    auth="<base64-encoded-api-key>",
)