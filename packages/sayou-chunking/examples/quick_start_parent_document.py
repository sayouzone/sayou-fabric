# ── Setup
"""
Create parent–child chunk pairs using `ParentDocumentSplitter`.

`ParentDocumentSplitter` implements the Parent Document Retrieval pattern:
it first splits the document into large **parent** chunks that preserve
broad context, then splits each parent into smaller **child** chunks
optimised for embedding similarity.

At query time, the retriever matches child chunks (small, precise) but
returns the parent chunk (large, contextually rich) to the language model.
This gives the model enough surrounding context to generate a grounded
answer while keeping the embedding comparison sharp.

Chunk hierarchy:

```
Document
  └─ Parent chunk 0  (large window — context carrier)
       ├─ Child chunk 0-0  (small window — embedding target)
       ├─ Child chunk 0-1
       └─ Child chunk 0-2
  └─ Parent chunk 1
       ├─ Child chunk 1-0
       └─ Child chunk 1-1
```
"""
import json

from sayou.chunking.pipeline import ChunkingPipeline
from sayou.chunking.splitter.parent_document_splitter import ParentDocumentSplitter

pipeline = ChunkingPipeline(extra_splitters=[ParentDocumentSplitter])
print("Pipeline initialized.")

LONG_TEXT = (
    """\
Retrieval-Augmented Generation (RAG) systems combine a retriever and a
language model.  The retriever finds relevant passages; the language model
generates an answer conditioned on those passages.

Chunking strategy is one of the most impactful design decisions in a RAG
pipeline.  Chunk too coarsely and retrieval becomes imprecise.  Chunk too
finely and you lose the surrounding context the model needs to reason.

The Parent Document strategy addresses this trade-off directly.  Small
child chunks are embedded and indexed; when a child chunk is retrieved the
system fetches its parent — a larger, semantically complete section — and
passes that to the language model.

Implementation in Sayou uses RecursiveSplitter for both levels.  The parent
uses a larger window; children subdivide each parent with a smaller window.
Every child stores a `parent_id` that points back to its parent chunk, and
every parent stores a `child_ids` list for forward navigation.
"""
    * 3
)  # repeat to ensure multiple parents


# ── Basic Parent–Child Split
"""
`parent_chunk_size` controls how large each parent window is.
`chunk_size` controls how large each child window is.

The pipeline returns parents and children interleaved in document order:
parent 0, children of parent 0, parent 1, children of parent 1, …
"""
chunks = pipeline.run(
    {
        "content": LONG_TEXT,
        "metadata": {"id": "rag_doc"},
        "config": {
            "parent_chunk_size": 600,
            "chunk_size": 150,
            "chunk_overlap": 0,
        },
    },
    strategy="parent_document",
)

parents = [c for c in chunks if c.metadata.get("doc_level") == "parent"]
children = [c for c in chunks if c.metadata.get("doc_level") == "child"]

print("=== Basic Parent–Child Split ===")
print(f"  Parents  : {len(parents)}")
print(f"  Children : {len(children)}")
print(f"  Total    : {len(chunks)}")


# ── Link Integrity
"""
Every child's `parent_id` matches a parent's `chunk_id`.
Every parent's `child_ids` contains the IDs of its children.
"""
parent_map = {p.metadata["chunk_id"]: p for p in parents}

print("\n=== Link Integrity ===")
for parent in parents:
    pid = parent.metadata["chunk_id"]
    child_ids = parent.metadata.get("child_ids", [])
    my_children = [c for c in children if c.metadata.get("parent_id") == pid]
    print(
        f"  {pid:30s}  children registered={len(child_ids)}  "
        f"children found={len(my_children)}"
    )


# ── Size Comparison
"""
Parents are significantly larger than children.  Print average sizes to
confirm the ratio matches the configured `parent_chunk_size` / `chunk_size`.
"""
avg_parent = sum(len(p.content) for p in parents) / max(len(parents), 1)
avg_child = sum(len(c.content) for c in children) / max(len(children), 1)

print("\n=== Size Comparison ===")
print(f"  Average parent length : {avg_parent:6.0f} chars")
print(f"  Average child length  : {avg_child:6.0f} chars")
print(f"  Ratio parent/child    : {avg_parent / max(avg_child, 1):.1f}x")


# ── Structure-based Parents
"""
Set `parent_strategy="structure"` to use `StructureSplitter` for the
parent pass.  This is useful when the document has clear section boundaries
(e.g. legislation, contracts, or API documentation) that should not be
split mid-section at the parent level.
"""
structured_chunks = pipeline.run(
    {
        "content": LONG_TEXT,
        "metadata": {"id": "rag_doc_structured"},
        "config": {
            "parent_chunk_size": 600,
            "chunk_size": 150,
            "chunk_overlap": 0,
            "parent_strategy": "structure",
        },
    },
    strategy="parent_document",
)

s_parents = [c for c in structured_chunks if c.metadata.get("doc_level") == "parent"]
s_children = [c for c in structured_chunks if c.metadata.get("doc_level") == "child"]

print("\n=== Structure-based Parents ===")
print(f"  Parents  : {len(s_parents)}")
print(f"  Children : {len(s_children)}")


# ── Save Results
"""
Save only child chunks — these are the units that get embedded and indexed.
Parents are stored separately for context retrieval at query time.
"""
output = {
    "parents": [p.model_dump() for p in parents],
    "children": [c.model_dump() for c in children],
}
with open("parent_document_chunks.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(
    f"\nSaved {len(parents)} parents and {len(children)} children to parent_document_chunks.json"
)
