!!! abstract "Source"
    Synced from [`packages/sayou-loader/examples/quick_start_chroma.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-loader/examples/quick_start_chroma.py).

## Setup

Load vector payloads into ChromaDB using `LoaderPipeline` with
`ChromaWriter`.

`ChromaWriter` supports two connection modes:

**Local** (PersistentClient)
    URI: ``chroma://<directory>/<collection_name>``
    Data is persisted to the local filesystem.

**Server** (HttpClient)
    URI: ``chroma://<host>:<port>/<collection_name>``
    Connects to a running Chroma server.

The writer calls ``collection.upsert()`` — safe to re-run on the same data.
Pre-computed vectors (``vector`` field) are attached automatically when
present; otherwise Chroma uses its default embedding function.

Install:

    pip install chromadb

```python
import json
import logging
from unittest.mock import MagicMock, patch

from sayou.loader.pipeline import LoaderPipeline
from sayou.loader.plugins.chroma_writer import ChromaWriter

pipeline = LoaderPipeline(extra_writers=[ChromaWriter])

PAYLOADS = [
    {
        "id": "sayou:doc:guide:c001",
        "vector": [0.12, 0.45, 0.78, 0.23, 0.91, 0.34, 0.56, 0.67],
        "text": "Sayou Fabric is a modular LLM data pipeline.",
        "metadata": {"node_class": "sayou:Text", "source": "guide.pdf", "page": 1},
    },
    {
        "id": "sayou:doc:guide:c002",
        "vector": [0.33, 0.71, 0.22, 0.88, 0.15, 0.49, 0.63, 0.07],
        "text": "Connector fetches data from 27 external sources.",
        "metadata": {"node_class": "sayou:Text", "source": "guide.pdf", "page": 2},
    },
    {
        "id": "sayou:doc:guide:c003",
        "vector": [0.55, 0.18, 0.92, 0.41, 0.76, 0.30, 0.14, 0.88],
        "text": "Chunking splits documents into retrieval-ready pieces.",
        "metadata": {"node_class": "sayou:Text", "source": "guide.pdf", "page": 3},
    },
]
```

## Write to Local ChromaDB

The writer detects a local path when there is no ``:`` before the first
``/`` in the URI path portion and uses ``PersistentClient``.

```python
mock_col = MagicMock()
mock_client = MagicMock()
mock_client.get_or_create_collection.return_value = mock_col

with patch("sayou.loader.plugins.chroma_writer.chromadb") as mock_chroma:
    mock_chroma.PersistentClient.return_value = mock_client

    result = pipeline.run(
        PAYLOADS,
        "chroma://./chroma_db/sayou_docs",
        strategy="ChromaWriter",
    )

print("=== Write to Local ChromaDB ===")
print(f"  Result          : {result}")
print(f"  upsert called   : {mock_col.upsert.called}")
call_kw = mock_col.upsert.call_args
if call_kw:
    ids = call_kw.kwargs.get("ids") or (call_kw.args[0] if call_kw.args else [])
    print(f"  IDs upserted    : {ids}")
```

## Write to ChromaDB Server

URI: ``chroma://<host>:<port>/<collection_name>``

The writer switches to ``HttpClient`` when it detects ``:`` (port) in
the path portion of the URI.

```python
print("\n=== URI Pattern Routing ===")
cw = ChromaWriter()
cw.logger = logging.getLogger("test")
cw._callbacks = []

cases = [
    ("chroma://./local/my_col", "PersistentClient", "./local", "my_col"),
    ("chroma://localhost:8000/my_col", "HttpClient", "localhost:8000", "my_col"),
]
for uri, mode, expected_path, expected_col in cases:
    path, col = cw._parse_destination(uri)
    print(f"  URI    : {uri}")
    print(f"  Mode   : {mode}  path={path!r}  collection={col!r}")
    assert path == expected_path and col == expected_col
```

## Metadata Sanitisation

ChromaDB only accepts str, int, float, bool in metadata.
`ChromaWriter._sanitize_metadata` converts incompatible types:

- ``None``  → excluded
- ``dict``  → JSON string
- ``list``  → JSON string (unless all elements are primitives)

```python
raw_meta = {
    "title": "Guide",
    "page": 1,
    "score": 0.95,
    "tags": ["llm", "pipeline"],  # list → JSON string
    "nested": {"source": "pdf"},  # dict → JSON string
    "empty": None,  # excluded
}
clean = cw._sanitize_metadata(raw_meta)

print("\n=== Metadata Sanitisation ===")
for k, v in clean.items():
    print(f"  {k:8s}: {v!r}  ({type(v).__name__})")
if "empty" not in clean:
    print("  empty  : (excluded — None)")
```

## Upsert with Pre-computed Vectors

When every payload has a ``vector`` field and the count matches ``ids``,
the writer calls ``upsert(ids=…, documents=…, metadatas=…, embeddings=…)``.

If vectors are missing or counts differ, it falls back to auto-embedding.

```python
print("\n=== Upsert Modes ===")
print("  All vectors present → upsert with embeddings")
print("  Vectors missing     → upsert with auto-embedding (Chroma default)")
```

## Real Connection

from sayou.loader.pipeline import LoaderPipeline
from sayou.loader.plugins.chroma_writer import ChromaWriter

pipeline = LoaderPipeline(extra_writers=[ChromaWriter])

# Local
pipeline.run(payloads, "chroma://./chroma_db/sayou_docs",
             strategy="ChromaWriter")

# Server
pipeline.run(payloads, "chroma://localhost:8000/sayou_docs",
             strategy="ChromaWriter", distance_func="cosine")