# ── Setup
"""
Split text by exact character count using `FixedLengthSplitter` and its
audited variant `AuditedFixedLengthSplitter`.

`FixedLengthSplitter` is the simplest splitter in the library.  It slices
the input string into windows of exactly `chunk_size` characters
(the last window may be shorter).  It ignores semantic boundaries — words
and sentences may be cut mid-way.

Use it when token-count precision matters more than readability, such as
when preparing training data for language models with strict context limits.

`AuditedFixedLengthSplitter` inherits the same slicing logic and adds an
`audit` dict to every chunk's metadata, recording when the chunk was
created, the original document length, and the splitter version.
"""
import json

from sayou.chunking.pipeline import ChunkingPipeline
from sayou.chunking.plugins.audited_fixed_length_splitter import (
    AuditedFixedLengthSplitter,
)

pipeline = ChunkingPipeline(extra_splitters=[AuditedFixedLengthSplitter])
print("Pipeline initialized.")

CONTENT = "ABCDEFGHIJ" * 10  # 100 chars for predictable demonstration


# ── Exact Split — No Overlap
"""
With `chunk_overlap=0` and `chunk_size=25`, 100 characters produce exactly
4 chunks of 25 characters each.

Each chunk carries `metadata` inherited from the input block.
"""
chunks = pipeline.run(
    {
        "content": CONTENT,
        "config": {"chunk_size": 25, "chunk_overlap": 0},
    },
    strategy="fixed_length",
)

print("=== Exact Split — No Overlap ===")
for i, chunk in enumerate(chunks):
    print(f"[{i}] len={len(chunk.content):3d}  {chunk.content!r}")


# ── Overlapping Windows
"""
`chunk_overlap` shifts the window start left by N characters so consecutive
chunks share a common tail/head region.

With `chunk_size=25` and `chunk_overlap=10`:
  step = 25 - 10 = 15
  windows start at 0, 15, 30, 45, …
"""
overlap_chunks = pipeline.run(
    {
        "content": CONTENT,
        "config": {"chunk_size": 25, "chunk_overlap": 10},
    },
    strategy="fixed_length",
)

print("\n=== Overlapping Windows ===")
for i, chunk in enumerate(overlap_chunks):
    print(f"[{i}] start={i*15:3d}  {chunk.content!r}")


# ── Real Text
"""
Fixed-length splitting on natural prose produces chunks that cut across
word and sentence boundaries.  This is intentional — the goal is uniform
token count, not readability.
"""
prose = (
    "The chunking strategy you choose affects retrieval quality significantly. "
    "Fixed-length splitting is fast and predictable but loses semantic coherence. "
    "Recursive splitting preserves paragraph structure. "
    "Semantic splitting groups sentences by topic similarity. "
    "Choose based on your downstream embedding model and retrieval task."
)

prose_chunks = pipeline.run(
    {"content": prose, "config": {"chunk_size": 80, "chunk_overlap": 20}},
    strategy="fixed_length",
)

print("\n=== Real Text ===")
for i, chunk in enumerate(prose_chunks):
    print(f"[{i}] {chunk.content!r}")


# ── Audited Variant
"""
`AuditedFixedLengthSplitter` adds an `audit` dict to `metadata`:

```python
{
    "processed_at": 1712000000.0,   # Unix timestamp
    "original_length": 100,          # char count of the source doc
    "splitter_version": "1.0.0"
}
```

Useful for data lineage tracking in production pipelines.
"""
audited_chunks = pipeline.run(
    {
        "content": CONTENT,
        "config": {"chunk_size": 25, "chunk_overlap": 0},
    },
    strategy="audited_fixed",
)

print("\n=== Audited Variant ===")
for i, chunk in enumerate(audited_chunks):
    audit = chunk.metadata.get("audit", {})
    print(
        f"[{i}] {chunk.content!r}  "
        f"| original_length={audit.get('original_length')}  "
        f"| version={audit.get('splitter_version')}"
    )


# ── Save Results
"""
Serialise both chunk sets to JSON for comparison.
"""
output = {
    "fixed_length": [c.model_dump() for c in chunks],
    "audited": [c.model_dump() for c in audited_chunks],
}
with open("fixed_length_chunks.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nSaved to fixed_length_chunks.json")
