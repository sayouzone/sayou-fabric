!!! abstract "Source"
    Synced from [`packages/sayou-chunking/examples/quick_start_recursive.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-chunking/examples/quick_start_recursive.py).

## Setup

Split plain text using `RecursiveSplitter`.

`RecursiveSplitter` is the general-purpose workhorse of the chunking
library.  It tries a priority-ordered list of separators — paragraph
break, line break, sentence boundary, word boundary — and falls back to
the next one whenever a separator fails to produce chunks small enough.

This guarantees that semantically related sentences stay together as long
as the `chunk_size` budget allows.

```python
import json

from sayou.chunking.pipeline import ChunkingPipeline

pipeline = ChunkingPipeline()
print("Pipeline initialized.")
```

## Basic Split

Pass `strategy="recursive"` with `chunk_size` inside `config`.

Each `SayouChunk` carries:
- `content`              — the text of this chunk (stripped)
- `metadata.chunk_id`    — unique identifier `{doc_id}_{index}`
- `metadata.part_index`  — zero-based position in the sequence
- `metadata.chunk_size`  — character count of this chunk

```python
text = """\
The Sayou Fabric is a collection of data-processing libraries designed for
the LLM era.  Each library handles one stage of the pipeline: collection,
parsing, refinement, chunking, wrapping, assembly, and loading.

At the top sits Brain, an orchestrator that coordinates all eight libraries.
Core provides the shared schemas and ontologies that underpin the whole system.

Chunking is the stage that breaks large documents into smaller pieces suitable
for embedding models.  Choosing the right strategy — recursive, semantic, or
structure-aware — directly affects retrieval quality downstream.
"""

chunks = pipeline.run(
    {"content": text, "config": {"chunk_size": 200, "chunk_overlap": 0}},
    strategy="recursive",
)

print("=== Basic Split ===")
for i, chunk in enumerate(chunks):
    print(f"[{i}] {len(chunk.content):4d} chars | {chunk.content[:60]!r}")
```

## Separator Priority

The default separator list is:

```python
["\\n\\n", "\\n", r"(?<=[.?!])\\s+", " ", ""]
```

You can override it with a custom list to match your document's structure.
For example, legal or regulatory text often uses numbered articles — split
on those first before falling back to paragraph breaks.

```python
legal_text = """\
Article 1. General Provisions
This agreement governs the use of the Sayou Fabric platform.
All users must comply with the terms set forth herein.

Article 2. Permitted Use
Users may integrate the platform into commercial products provided that
attribution is maintained in documentation and user-facing materials.

Article 3. Prohibited Actions
Reverse engineering, redistribution without permission, and sublicensing
are strictly prohibited under this agreement.
"""

legal_chunks = pipeline.run(
    {
        "content": legal_text,
        "config": {
            "chunk_size": 300,
            "chunk_overlap": 0,
            "separators": [r"Article \d+\.", r"\n\n", r"\n", " ", ""],
        },
    },
    strategy="recursive",
)

print("\n=== Separator Priority ===")
for i, chunk in enumerate(legal_chunks):
    print(f"[{i}] {chunk.content[:80]!r}")
```

## Overlap

`chunk_overlap` repeats the tail of the previous chunk at the start of
the next one.  This preserves cross-boundary context for embedding models.

Use overlap when the document has long sentences that may straddle chunk
boundaries, such as meeting transcripts or technical reports.

```python
overlap_chunks = pipeline.run(
    {
        "content": text,
        "config": {"chunk_size": 200, "chunk_overlap": 50},
    },
    strategy="recursive",
)

print("\n=== Overlap ===")
for i, chunk in enumerate(overlap_chunks):
    print(f"[{i}] len={len(chunk.content):4d}  start={chunk.content[:40]!r}")
```

## Save Results

Serialise all chunks to JSON for inspection or downstream processing.

```python
output = [c.model_dump() for c in chunks]
with open("recursive_chunks.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nSaved {len(output)} chunks to recursive_chunks.json")
```