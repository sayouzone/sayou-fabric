!!! abstract "Source"
    Synced from [`packages/sayou-refinery/examples/quick_start_raw_json.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-refinery/examples/quick_start_raw_json.py).

## Setup

Normalise raw JSON data into `record` SayouBlocks using
`RefineryPipeline` with `RawJsonNormalizer`.

`RawJsonNormalizer` is the simplest normaliser for structured data.
It accepts a single `dict` or a `list[dict]` and wraps each dictionary
into a `SayouBlock` of type `"record"`.  No content/metadata separation
is performed — the entire dict becomes the block content.

Use `RawJsonNormalizer` when:
- You have a flat API response and just want each record as a block.
- You do not need automatic id extraction or content/meta separation.
- You want the raw structure preserved exactly as-is.

For smarter handling (id extraction, content/meta split, transcript
batching), use `RecordNormalizer` instead.

```python
import json

from sayou.refinery.normalizer.raw_json_normalizer import RawJsonNormalizer
from sayou.refinery.pipeline import RefineryPipeline

pipeline = RefineryPipeline(extra_normalizers=[RawJsonNormalizer])
```

## Single Dict

A single `dict` becomes one `SayouBlock(type="record")`.

`block.content` is the dict itself.
`block.metadata` always contains:
- `source_type`: `"raw_json"`
- `normalization_strategy`: `"RawJsonNormalizer"`

```python
record = {
    "id": "product-001",
    "name": "Sayou Fabric Pro",
    "price": 99.99,
    "tags": ["llm", "pipeline", "data"],
}

blocks = pipeline.run(record, strategy="raw_json")

print("=== Single Dict ===")
print(f"  Block count : {len(blocks)}")
print(f"  Type        : {blocks[0].type}")
print(f"  Content     : {blocks[0].content}")
print(f"  Metadata    : {blocks[0].metadata}")
```

## List of Dicts

A `list[dict]` produces one block per item.
This is the primary use case — database rows, API result sets, CSV data.

Each block is independent with its own copy of the normaliser metadata.

```python
products = [
    {"id": "p-001", "name": "Connector Pack", "price": 29.99},
    {"id": "p-002", "name": "Chunking Engine", "price": 49.99},
    {"id": "p-003", "name": "Fabric Pro", "price": 99.99},
]

list_blocks = pipeline.run(products, strategy="raw_json")

print("\n=== List of Dicts ===")
print(f"  Input items : {len(products)}")
print(f"  Output blocks: {len(list_blocks)}")
for b in list_blocks:
    print(f"  [{b.content['id']}] {b.content['name']}  ${b.content['price']}")
```

## Nested Structures

`RawJsonNormalizer` recursively converts Pydantic models and custom
objects into plain Python types before wrapping, so nested structures
are safe to pass in.

All values are preserved exactly — no keys are moved to metadata.

```python
nested = {
    "order_id": "ord-789",
    "customer": {"name": "Alice", "email": "alice@example.com"},
    "items": [{"sku": "A1", "qty": 2}, {"sku": "B3", "qty": 1}],
    "total": 149.98,
}

nested_blocks = pipeline.run(nested, strategy="raw_json")

print("\n=== Nested Structures ===")
b = nested_blocks[0]
print(f"  order_id : {b.content['order_id']}")
print(f"  customer : {b.content['customer']}")
print(f"  items    : {b.content['items']}")
```

## Non-dict Items are Skipped

If a list contains non-dict items (strings, numbers), they are silently
skipped with a warning log.  Only `dict` items produce blocks.

```python
mixed = [
    {"id": "1", "value": "valid"},
    "this is a string",
    42,
    {"id": "2", "value": "also valid"},
]

mixed_blocks = pipeline.run(mixed, strategy="raw_json")

print("\n=== Non-dict Items Skipped ===")
print(f"  Input items  : {len(mixed)}")
print(f"  Output blocks: {len(mixed_blocks)}  (2 dicts only)")
```

## Save Results

```python
output = [b.model_dump() for b in list_blocks]
with open("raw_json_blocks.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nSaved {len(list_blocks)} block(s) to 'raw_json_blocks.json'")
```