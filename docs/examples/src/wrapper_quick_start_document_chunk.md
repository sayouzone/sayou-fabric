!!! abstract "Source"
    Synced from [`packages/sayou-wrapper/examples/quick_start_document_chunk.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-wrapper/examples/quick_start_document_chunk.py).

## Setup

Convert sayou-chunking output into semantic SayouNodes using
`WrapperPipeline` with `DocumentChunkAdapter`.

`DocumentChunkAdapter` maps `SayouChunk` objects (or plain dicts with the
same fields) into typed `SayouNode` objects.  It:

- Derives a deterministic URI from `chunk_id` and source filename
- Maps `semantic_type` → ontology class (Text, Topic, Table, CodeBlock, …)
- Preserves `parent_id` as a `sayou:hasParent` relationship
- Forwards all other metadata as passthrough attributes (`meta:*`)

Install dependencies before running with real data:

    pip install sayou-wrapper sayou-core

```python
import json

from sayou.wrapper.adapter.document_chunk_adapter import DocumentChunkAdapter
from sayou.wrapper.pipeline import WrapperPipeline

pipeline = WrapperPipeline(extra_adapters=[DocumentChunkAdapter])
```

## Basic Conversion

Pass a list of chunk dicts (or SayouChunk objects).
Each chunk becomes one SayouNode with a deterministic URI:

    sayou:doc:<safe_filename>:<chunk_id>

```python
chunks = [
    {
        "content": "Sayou Fabric is a collection of LLM data-processing libraries.",
        "metadata": {
            "chunk_id": "c001",
            "source": "overview.pdf",
            "semantic_type": "text",
            "page_num": 1,
        },
    },
    {
        "content": "## Architecture\n\nEight libraries coordinate through Brain.",
        "metadata": {
            "chunk_id": "c002",
            "source": "overview.pdf",
            "semantic_type": "heading",
            "is_header": True,
            "page_num": 1,
        },
    },
    {
        "content": "| Library   | Role        |\n| Connector | Collection  |",
        "metadata": {
            "chunk_id": "c003",
            "source": "overview.pdf",
            "semantic_type": "table",
            "page_num": 2,
        },
    },
]

output = pipeline.run(chunks, strategy="document_chunk")

print("=== Basic Conversion ===")
print(f"  Input chunks : {len(chunks)}")
print(f"  Output nodes : {len(output.nodes)}")
for node in output.nodes:
    print(f"  [{node.node_class.split(':')[-1]:12s}] {node.node_id}")
```

## Semantic Type Mapping

Mapping table:

| semantic_type | is_header | node_class          |
|---------------|-----------|---------------------|
| (any)         | True      | sayou:Topic         |
| table         | False     | sayou:Table         |
| code_block    | False     | sayou:CodeBlock     |
| list_item     | False     | sayou:ListItem      |
| (other)       | False     | sayou:Text          |

```python
print("\n=== Semantic Type Mapping ===")
for node in output.nodes:
    text = str(node.attributes.get("schema:text", ""))[:40]
    print(f"  {node.node_class:22s}  {text!r}")
```

## Parent-Child Relationships

When a chunk has `parent_id` in metadata, the adapter creates a
`sayou:hasParent` relationship — useful for parent-document chunking.

```python
parent_chunks = [
    {
        "content": "Chapter 1: Introduction to Sayou Fabric.",
        "metadata": {"chunk_id": "parent-1", "source": "guide.pdf"},
    },
    {
        "content": "Sayou Fabric consists of eight specialised libraries.",
        "metadata": {
            "chunk_id": "child-1",
            "source": "guide.pdf",
            "parent_id": "parent-1",
        },
    },
    {
        "content": "Each library handles one stage of the data pipeline.",
        "metadata": {
            "chunk_id": "child-2",
            "source": "guide.pdf",
            "parent_id": "parent-1",
        },
    },
]

parent_output = pipeline.run(parent_chunks, strategy="document_chunk")

print("\n=== Parent-Child Relationships ===")
for node in parent_output.nodes:
    if node.relationships:
        parent_uri = node.relationships.get("sayou:hasParent", [None])[0]
        print(f"  {node.node_id}")
        print(f"    sayou:hasParent → {parent_uri}")
    else:
        print(f"  {node.node_id}  (root)")
```

## Metadata Passthrough

Any metadata key not handled by the adapter is stored as `meta:<key>`.
Downstream builders (e.g. CodeGraphBuilder) read these passthrough attrs.

```python
code_chunk = {
    "content": "def process(data): return data",
    "metadata": {
        "chunk_id": "code-001",
        "semantic_type": "code_block",
        "language": "python",
        "line_start": 10,
        "line_end": 11,
    },
}

code_output = pipeline.run([code_chunk], strategy="document_chunk")
node = code_output.nodes[0]

print("\n=== Metadata Passthrough ===")
for k, v in node.attributes.items():
    if k.startswith("meta:"):
        print(f"  {k}: {v}")
```

## Save Results

```python
result = {
    "nodes": [
        {
            "node_id": n.node_id,
            "node_class": n.node_class,
            "relationships": n.relationships,
        }
        for n in output.nodes
    ]
}
with open("document_chunk_nodes.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"\nSaved {len(output.nodes)} node(s) to 'document_chunk_nodes.json'")
```