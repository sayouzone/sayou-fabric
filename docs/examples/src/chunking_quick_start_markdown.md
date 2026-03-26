!!! abstract "Source"
    Synced from [`packages/sayou-chunking/examples/quick_start_markdown.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-chunking/examples/quick_start_markdown.py).

## Setup

Split Markdown documents using `MarkdownSplitter`.

`MarkdownSplitter` understands the structure of Markdown.  It first splits
on headers (`#`, `##`, `###`, …), creating one chunk per heading, and then
recursively splits the body text beneath each header if it exceeds
`chunk_size`.

Every chunk is enriched with semantic metadata so downstream retrieval
systems can reconstruct document hierarchy, navigate to the correct section,
or filter by heading level.

Protected patterns prevent code fences (`` ``` ``), tables, and base64
images from being torn apart mid-block.

```python
import json

from sayou.chunking.pipeline import ChunkingPipeline
from sayou.chunking.plugins.markdown_splitter import MarkdownSplitter

pipeline = ChunkingPipeline(extra_splitters=[MarkdownSplitter])
print("Pipeline initialized.")

MARKDOWN = """\
# Sayou Fabric Overview

Sayou Fabric is a collection of data-processing libraries for the LLM era.

## Architecture

The system is composed of eight libraries coordinated by Brain.

### Connector

Connector collects raw data from external sources: files, databases,
APIs, and SaaS platforms.

### Chunking

Chunking breaks documents into retrieval-ready pieces.
It supports recursive, semantic, code-aware, and structure-aware strategies.

## Getting Started

Install the core package and at least one library:

```bash
pip install sayou-core sayou-chunking
```

Then initialise a pipeline and call `run()`.

## Data Flow

| Stage      | Library   | Output       |
|------------|-----------|--------------|
| Collect    | Connector | SayouPacket  |
| Parse      | Document  | SayouBlock   |
| Refine     | Refinery  | SayouBlock   |
| Chunk      | Chunking  | SayouChunk   |
"""
```

## Header Chunking

Each Markdown heading becomes one `SayouChunk` with:

| metadata key      | value                           |
|-------------------|---------------------------------|
| `is_header`       | `True`                          |
| `semantic_type`   | `"h1"` / `"h2"` / `"h3"` / … |
| `level`           | heading depth as integer        |
| `chunk_id`        | unique string id                |

Body text beneath a heading becomes a sibling chunk with:

| metadata key      | value                                   |
|-------------------|-----------------------------------------|
| `parent_id`       | `chunk_id` of the preceding header      |
| `section_title`   | plain text of the preceding heading     |
| `semantic_type`   | `"text"`, `"table"`, `"code_block"`, … |

```python
chunks = pipeline.run(
    {"content": MARKDOWN, "config": {"chunk_size": 500}},
    strategy="markdown",
)

print("=== Header Chunking ===")
for chunk in chunks:
    is_hdr = chunk.metadata.get("is_header", False)
    s_type = chunk.metadata.get("semantic_type", "")
    level = chunk.metadata.get("level", "")
    parent = chunk.metadata.get("section_title", "")
    tag = f"H{level}" if is_hdr else f"body [{s_type}]"
    print(f"  {tag:20s} | parent={parent!r:30s} | {chunk.content[:50]!r}")
```

## Semantic Type Classification

Body chunks are classified into semantic types:

- `"text"`       — plain prose
- `"code_block"` — content starting with `` ``` ``
- `"table"`      — content starting with `|`
- `"list_item"`  — content starting with `- ` or `* `

Use `semantic_type` to apply different embedding strategies per content type
— code blocks and tables often benefit from specialised encoders.

```python
code_chunks = [c for c in chunks if c.metadata.get("semantic_type") == "code_block"]
table_chunks = [c for c in chunks if c.metadata.get("semantic_type") == "table"]
text_chunks = [c for c in chunks if c.metadata.get("semantic_type") == "text"]

print(f"\n=== Semantic Type Distribution ===")
print(f"  text blocks  : {len(text_chunks)}")
print(f"  code blocks  : {len(code_chunks)}")
print(f"  table blocks : {len(table_chunks)}")
```

## Header Hierarchy

Collect all header chunks and print the document outline.
The heading level is stored as an integer in `metadata["level"]`.

```python
headers = [c for c in chunks if c.metadata.get("is_header")]
print("\n=== Document Outline ===")
for h in headers:
    indent = "  " * (h.metadata["level"] - 1)
    print(f"  {indent}{'#' * h.metadata['level']} {h.content}")
```

## Small chunk_size Triggers Sub-splitting

When body content exceeds `chunk_size`, `MarkdownSplitter` recursively
splits it using the standard separator list.  The resulting sub-chunks
all share the same `parent_id` and `section_title`.

```python
fine_chunks = pipeline.run(
    {"content": MARKDOWN, "config": {"chunk_size": 100}},
    strategy="markdown",
)

body_chunks = [c for c in fine_chunks if not c.metadata.get("is_header")]
print(f"\n=== Sub-splitting at chunk_size=100 ===")
print(f"  Total chunks : {len(fine_chunks)}")
print(f"  Header chunks: {len(fine_chunks) - len(body_chunks)}")
print(f"  Body chunks  : {len(body_chunks)}")
```

## Save Results

Serialise all chunks to JSON.  Each entry includes `content`, `metadata`,
and the full `model_dump()` structure.

```python
with open("markdown_chunks.json", "w", encoding="utf-8") as f:
    json.dump([c.model_dump() for c in chunks], f, indent=2, ensure_ascii=False)

print(f"\nSaved {len(chunks)} chunks to markdown_chunks.json")
```