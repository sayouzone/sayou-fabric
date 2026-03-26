!!! abstract "Source"
    Synced from [`packages/sayou-chunking/examples/quick_start_langchain.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-chunking/examples/quick_start_langchain.py).

## Setup

Split text using LangChain's `RecursiveCharacterTextSplitter` via
`LangchainSplitter`.

`LangchainSplitter` is an adapter that delegates to LangChain's splitter
while keeping the result in Sayou's `SayouChunk` schema.  Use it when
you are migrating an existing LangChain-based pipeline to Sayou, or when
you want to compare LangChain's output directly with Sayou's own splitters.

Install the optional dependency before running:

```bash
pip install langchain-text-splitters
python quick_start_langchain.py
```

If `langchain-text-splitters` is not installed, `LangchainSplitter` raises
`ImportError` when first called.  The example handles this gracefully.

```python
import json

from sayou.chunking.pipeline import ChunkingPipeline
from sayou.chunking.plugins.langchain_splitter import LangchainSplitter

pipeline = ChunkingPipeline(extra_splitters=[LangchainSplitter])
print("Pipeline initialized.")

TEXT = """\
LangChain is a framework for building applications with language models.
It provides abstractions for chains, agents, memory, and retrieval.
Many production RAG systems started with LangChain before migrating to
lighter-weight or more specialised alternatives.

Sayou Fabric's LangchainSplitter lets you use LangChain's text splitter
as a drop-in within the Sayou pipeline.  The output is identical to
calling RecursiveCharacterTextSplitter directly, but the result is wrapped
in SayouChunk objects that carry Sayou's standard metadata schema.

This makes it easy to run A/B comparisons between LangChain splitting and
Sayou's own RecursiveSplitter without rewriting the rest of your pipeline.
"""
```

## Basic Split

`strategy="langchain_recursive"` routes to `LangchainSplitter`.
`chunk_size` and `chunk_overlap` are forwarded directly to
`RecursiveCharacterTextSplitter`.

Each `SayouChunk.content` is the raw text produced by LangChain.
`SayouChunk.metadata` is inherited from the input block.

```python
try:
    chunks = pipeline.run(
        {
            "content": TEXT,
            "config": {
                "chunk_size": 200,
                "chunk_overlap": 50,
                "separators": ["\n\n", "\n", ". ", " ", ""],
            },
        },
        strategy="langchain_recursive",
    )

    print("=== Basic Split ===")
    for i, chunk in enumerate(chunks):
        print(f"  [{i}] {len(chunk.content):4d} chars | {chunk.content[:70]!r}")

except ImportError as e:
    print(f"  [SKIP] {e}")
    print("  Run: pip install langchain-text-splitters")
    chunks = []
```

## Custom Separators

LangChain's splitter supports the same separator priority list as Sayou's
`RecursiveSplitter`.  Pass `separators` in `config` to customise the
split hierarchy.

For code or markdown with mixed content, use a separator list that
prioritises structural delimiters before whitespace.

```python
try:
    code_text = """\
def process_data(items):
    results = []
    for item in items:
        if item > 0:
            results.append(item * 2)
    return results

def save_results(path, data):
    with open(path, "w") as f:
        import json
        json.dump(data, f, indent=2)
"""

    code_chunks = pipeline.run(
        {
            "content": code_text,
            "config": {
                "chunk_size": 120,
                "chunk_overlap": 20,
                "separators": ["\n\ndef ", "\ndef ", "\n    ", "\n", " "],
            },
        },
        strategy="langchain_recursive",
    )

    print("\n=== Custom Separators (code) ===")
    for i, chunk in enumerate(code_chunks):
        print(f"  [{i}] {chunk.content[:80]!r}")

except ImportError:
    print("\n  [SKIP] langchain-text-splitters not installed.")
```

## Comparison: LangChain vs Sayou RecursiveSplitter

Run the same text through both splitters and compare chunk counts and sizes.
The results should be similar but may differ in boundary placement due to
implementation differences in how the separators are applied.

```python
from sayou.chunking.splitter.recursive_splitter import RecursiveSplitter

pipeline_sayou = ChunkingPipeline()

sayou_chunks = pipeline_sayou.run(
    {
        "content": TEXT,
        "config": {"chunk_size": 200, "chunk_overlap": 50},
    },
    strategy="recursive",
)

print("\n=== Comparison ===")
print(f"  Sayou RecursiveSplitter : {len(sayou_chunks)} chunk(s)")
if chunks:
    print(f"  LangchainSplitter       : {len(chunks)} chunk(s)")
else:
    print(f"  LangchainSplitter       : (not installed)")
```

## Save Results

Save both results to JSON only when both splitters ran successfully.

```python
if chunks:
    output = {
        "langchain": [c.model_dump() for c in chunks],
        "sayou_recursive": [c.model_dump() for c in sayou_chunks],
    }
    with open("langchain_chunks.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to langchain_chunks.json")
else:
    print("\nInstall langchain-text-splitters to generate the output file.")
```