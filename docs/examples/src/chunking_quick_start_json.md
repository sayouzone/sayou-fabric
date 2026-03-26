!!! abstract "Source"
    Synced from [`packages/sayou-chunking/examples/quick_start_json.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-chunking/examples/quick_start_json.py).

## Setup

Split JSON data using `JsonSplitter`.

`JsonSplitter` operates on structured data rather than plain text.  It
accepts a JSON string, a Python `list`, or a Python `dict` as `content`
and groups items into chunks whose serialised size stays under
`chunk_size` bytes.

Two routing modes:

| Input type | Strategy                            | chunk_type metadata |
|------------|-------------------------------------|---------------------|
| `list`     | Batch consecutive items             | `"json_list"`       |
| `dict`     | Batch key-value pairs               | `"json_object"`     |

Oversized items within a list are split further using the dict strategy.
Oversized values within a dict are split recursively by key.

Use `JsonSplitter` for structured records from databases, API responses,
transcript cue lists, or any other tabular data.

```python
import json

from sayou.chunking.pipeline import ChunkingPipeline
from sayou.chunking.plugins.json_splitter import JsonSplitter

pipeline = ChunkingPipeline(extra_splitters=[JsonSplitter])
print("Pipeline initialized.")
```

## Split a JSON Array

The most common use case: a list of records fetched from a database or API.

Each chunk contains as many consecutive items as fit within `chunk_size`
characters (after JSON serialisation).  Metadata records:

- `chunk_type`    — `"json_list"`
- `item_count`    — number of items in this chunk
- `index_start`   — first item's original index
- `index_end`     — last item's original index

```python
records = [
    {"id": i, "name": f"user_{i:03d}", "score": round(i * 1.7, 2)} for i in range(30)
]

chunks = pipeline.run(
    {
        "content": json.dumps(records),
        "config": {"chunk_size": 300, "chunk_overlap": 0},
    },
    strategy="json",
)

print("=== Split a JSON Array ===")
for chunk in chunks:
    m = chunk.metadata
    print(
        f"  items {m['index_start']:2d}–{m['index_end']:2d}  "
        f"count={m['item_count']}  "
        f"bytes={len(chunk.content):4d}"
    )

total = sum(c.metadata["item_count"] for c in chunks)
print(f"  Total items recovered: {total} / {len(records)}")
```

## Split a JSON Object

A large dict is split by key — key-value pairs are batched until the
serialised size reaches `chunk_size`.  Each chunk carries:

- `chunk_type`       — `"json_object"`
- `chunk_id_suffix`  — `"part_0"`, `"part_1"`, …

Useful for wide API responses, configuration objects, or document metadata
dicts that are too large to embed in a single call.

```python
large_dict = {f"field_{i:03d}": "x" * 40 for i in range(20)}

dict_chunks = pipeline.run(
    {
        "content": json.dumps(large_dict),
        "config": {"chunk_size": 200},
    },
    strategy="json",
)

print("\n=== Split a JSON Object ===")
for chunk in dict_chunks:
    keys = list(json.loads(chunk.content).keys())
    print(f"  suffix={chunk.metadata['chunk_id_suffix']:8s}  keys={keys}")
```

## Transcript Cue Lists

YouTube and podcast transcripts are delivered as lists of timed cue dicts:

```python
[{"text": "Hello.", "start": 0.0, "duration": 1.5}, …]
```

`JsonSplitter` batches consecutive cues until the chunk reaches `chunk_size`.
When a `"start"` key is present, `metadata` also records:

- `sayou:startTime` — start time of the first cue in the chunk
- `sayou:endTime`   — end time of the last cue in the chunk

```python
transcript = [
    {"text": f"Sentence {i}.", "start": i * 3.0, "duration": 2.8} for i in range(20)
]

transcript_chunks = pipeline.run(
    {
        "content": json.dumps(transcript),
        "config": {"chunk_size": 400},
    },
    strategy="json",
)

print("\n=== Transcript Cue Lists ===")
for chunk in transcript_chunks:
    m = chunk.metadata
    print(
        f"  cues {m['index_start']:2d}–{m['index_end']:2d}  "
        f"start={m.get('sayou:startTime', '?'):5}s  "
        f"end={m.get('sayou:endTime', '?'):5}s"
    )
```

## Block Type Input

Pass `type="json"` in the block so `JsonSplitter.can_handle()` returns 1.0
without needing the explicit `strategy="json"` argument.

```python
from sayou.core.schemas import SayouBlock

block = SayouBlock(
    type="json",
    content=json.dumps(records[:10]),
    metadata={"config": {"chunk_size": 200}, "source": "api_response"},
)

auto_chunks = pipeline.run(block, strategy="auto")
print(f"\n=== Block Type Input (auto) ===")
print(f"  Chunks: {len(auto_chunks)}")
for c in auto_chunks:
    print(f"    item_count={c.metadata['item_count']}  bytes={len(c.content)}")
```

## Save Results

Write all list chunks to JSON for downstream processing.

```python
with open("json_chunks.json", "w", encoding="utf-8") as f:
    json.dump([c.model_dump() for c in chunks], f, indent=2, ensure_ascii=False)

print(f"\nSaved {len(chunks)} chunks to json_chunks.json")
```