!!! abstract "Source"
    Synced from [`packages/sayou-refinery/examples/quick_start_record.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-refinery/examples/quick_start_record.py).

## Setup

Normalise structured records into `SayouBlock` objects using
`RefineryPipeline` with `RecordNormalizer`.

`RecordNormalizer` is the smart normaliser for structured data.
Unlike `RawJsonNormalizer`, it understands the Sayou data envelope:

```python
{
    "content":  <heavy payload>,   # list or dict — becomes block.content
    "meta":     <lightweight kv>,  # becomes block.metadata
}
```

It also:
- Extracts `id`, `_id`, `uuid`, `video_id`, `uid` into `metadata["original_id"]`
- Wraps a homogeneous `list[dict]` into a single block (transcript pattern)
- Recursively converts Pydantic models and custom objects to plain types

Supported strategies: `"json"`, `"record"`, `"dict"`, `"db"`

```python
import json

from sayou.refinery.normalizer.record_normalizer import RecordNormalizer
from sayou.refinery.pipeline import RefineryPipeline

pipeline = RefineryPipeline(extra_normalizers=[RecordNormalizer])
```

## Single Record

A plain dict without `content`/`meta` keys is wrapped as-is.
`original_id` is extracted automatically from common id field names.

```python
user = {"id": "u-001", "name": "Alice", "email": "alice@example.com", "score": 95}

blocks = pipeline.run(user, strategy="record")

print("=== Single Record ===")
b = blocks[0]
print(f"  Type        : {b.type}")
print(f"  Content     : {b.content}")
print(f"  original_id : {b.metadata.get('original_id')}")
```

## Content / Meta Envelope

When the input has both a `content` key and a `meta` key, they are
separated automatically.

- `content` → `block.content`
- `meta`    → `block.metadata`

This is the standard output format from `ConnectorPipeline`, so
`RecordNormalizer` is the natural next step after collection.

```python
packet = {
    "content": [
        {"text": "Hello and welcome.", "start": 0.0, "duration": 2.5},
        {"text": "Today we cover RAG.", "start": 2.5, "duration": 3.0},
        {"text": "Let's start.", "start": 5.5, "duration": 1.8},
    ],
    "meta": {
        "source": "youtube",
        "video_id": "dQw4w9WgXcQ",
        "title": "RAG Pipeline Tutorial",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    },
}

envelope_blocks = pipeline.run(packet, strategy="record")

print("\n=== Content / Meta Envelope ===")
b = envelope_blocks[0]
print(f"  Content type    : {type(b.content).__name__}")
print(f"  Cue count       : {len(b.content)}")
print(f"  metadata source : {b.metadata.get('source')}")
print(f"  metadata video_id: {b.metadata.get('video_id')}")
print(f"  original_id     : {b.metadata.get('original_id')}")
```

## Database Rows

A list of dicts from a database query (e.g. `MySQLFetcher` output) is
detected as a homogeneous list and wrapped into a single block.

`metadata["record_count"]` records how many rows are in the batch.

```python
db_rows = [
    {"id": 1, "product": "Widget A", "revenue": 12000, "region": "APAC"},
    {"id": 2, "product": "Widget B", "revenue": 8500, "region": "EMEA"},
    {"id": 3, "product": "Widget C", "revenue": 15000, "region": "APAC"},
]

row_blocks = pipeline.run(db_rows, strategy="record")

print("\n=== Database Rows ===")
b = row_blocks[0]
print(f"  Block count  : {len(row_blocks)}")
print(f"  record_count : {b.metadata.get('record_count')}")
print(f"  First row    : {b.content[0] if isinstance(b.content, list) else b.content}")
```

## ID Extraction

`RecordNormalizer` looks for id fields in this priority order:
`id` → `_id` → `uuid` → `video_id` → `uid` → `original_id`

The found value is copied into `metadata["original_id"]` as a string,
regardless of whether it came from `meta` or `content`.

```python
records_with_ids = [
    {"id": "plain-id", "name": "uses id"},
    {"_id": "mongo-id", "name": "uses _id"},
    {"uuid": "uuid-val", "name": "uses uuid"},
    {"video_id": "yt-id", "name": "uses video_id"},
]

print("\n=== ID Extraction ===")
for rec in records_with_ids:
    b = pipeline.run(rec, strategy="record")[0]
    print(
        f"  {list(rec.keys())[0]:10s} → original_id={b.metadata.get('original_id')!r}"
    )
```

## Pydantic Model Input

Pydantic models are automatically converted to plain dicts before
normalisation — no manual `.model_dump()` call needed.

```python
try:
    from pydantic import BaseModel

    class Product(BaseModel):
        id: str
        name: str
        price: float

    product = Product(id="prd-42", name="Sayou Loader", price=59.99)
    pyd_blocks = pipeline.run(product, strategy="record")

    print("\n=== Pydantic Model Input ===")
    print(f"  Content : {pyd_blocks[0].content}")
except Exception as e:
    print(f"\n=== Pydantic Model Input === (skipped: {e})")
```

## Save Results

```python
output = [b.model_dump() for b in envelope_blocks]
with open("record_blocks.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nSaved {len(envelope_blocks)} block(s) to 'record_blocks.json'")
```