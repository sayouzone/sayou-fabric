!!! abstract "Source"
    Synced from [`packages/sayou-wrapper/examples/quick_start_code_chunk.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-wrapper/examples/quick_start_code_chunk.py).

## Setup

Convert code SayouChunks into a typed, hierarchical node graph using
`WrapperPipeline` with `CodeChunkAdapter`.

`CodeChunkAdapter` is the bridge between `sayou-chunking` (Python/JS/…
language splitters) and `sayou-assembler` (CodeGraphBuilder).

It performs a two-pass build:

**Pass 1 — Node creation**
Each chunk becomes a typed node based on `semantic_type`:

| semantic_type    | node_class           | node_id pattern                        |
|------------------|----------------------|----------------------------------------|
| ``class_header`` | ``sayou:Class``      | ``sayou:class:<path>::<ClassName>``    |
| ``method``       | ``sayou:Method``     | ``sayou:method:<path>::<Class.method>``|
| ``function``     | ``sayou:Function``   | ``sayou:func:<path>::<func_name>``     |
| ``class_attributes`` | ``sayou:AttributeBlock`` | ``sayou:attrs:<path>::<Class.attrs>``|
| (other)          | ``sayou:CodeBlock``  | ``sayou:block:<path>::<index>``        |

A ``sayou:File`` node is also created (once per unique source path).

**Pass 2 — Hierarchy injection**
Class nodes receive ``sayou:contains`` edges pointing to their child
methods and attribute blocks.  Method/attribute nodes receive
``sayou:hasParent`` back-links to their class.

**Stable IDs**
Node IDs are based on symbol names (`ClassName.method_name`), not line
numbers, so they survive minor refactors.

**Call-graph forwarding**
Raw call-graph metadata (`calls`, `attribute_calls`, `type_refs`, …)
extracted by the language splitter is forwarded as node attributes so
`CodeGraphBuilder` can resolve them into typed edges without re-parsing.

```python
import json

from sayou.core.schemas import SayouChunk

from sayou.wrapper.pipeline import WrapperPipeline
from sayou.wrapper.plugins.code_chunk_adapter import CodeChunkAdapter

pipeline = WrapperPipeline(extra_adapters=[CodeChunkAdapter])
```

## Sample Code Chunks

These chunks replicate the output of `sayou-chunking`'s `PythonSplitter`
applied to a small Python file.  In production they come from
`ChunkingPipeline.run(source_code, strategy="python")`.

```python
SOURCE_PATH = "sayou/refinery/pipeline.py"

chunks = [
    # File-level imports block
    SayouChunk(
        content="import importlib\nimport pkgutil\nfrom typing import Dict, List",
        metadata={
            "semantic_type": "code_block",
            "source": SOURCE_PATH,
            "language": "python",
            "chunk_index": 0,
            "lineStart": 1,
            "lineEnd": 3,
            "imports": [
                {"module": "importlib", "name": None, "level": 0},
                {"module": "pkgutil", "name": None, "level": 0},
                {"module": "typing", "name": "Dict", "level": 0},
                {"module": "typing", "name": "List", "level": 0},
            ],
        },
    ),
    # Class header
    SayouChunk(
        content='class RefineryPipeline(BaseComponent):\n    """Orchestrates the refinery stage."""',
        metadata={
            "semantic_type": "class_header",
            "source": SOURCE_PATH,
            "language": "python",
            "class_name": "RefineryPipeline",
            "inherits_from": ["BaseComponent"],
            "instance_attrs": [
                "normalizer_cls_map",
                "processor_cls_map",
                "global_config",
            ],
            "lineStart": 6,
            "lineEnd": 7,
        },
    ),
    # Class attributes block
    SayouChunk(
        content="    component_name = 'RefineryPipeline'",
        metadata={
            "semantic_type": "class_attributes",
            "source": SOURCE_PATH,
            "language": "python",
            "parent_node": "RefineryPipeline",
            "lineStart": 8,
            "lineEnd": 8,
        },
    ),
    # __init__ method
    SayouChunk(
        content="    def __init__(self, extra_normalizers=None, **kwargs):\n        super().__init__()\n        self.normalizer_cls_map = {}",
        metadata={
            "semantic_type": "method",
            "source": SOURCE_PATH,
            "language": "python",
            "parent_node": "RefineryPipeline",
            "function_name": "__init__",
            "params": [
                {"name": "self", "kind": "POSITIONAL_OR_KEYWORD"},
                {
                    "name": "extra_normalizers",
                    "kind": "POSITIONAL_OR_KEYWORD",
                    "has_default": True,
                },
            ],
            "calls": ["super"],
            "lineStart": 10,
            "lineEnd": 12,
        },
    ),
    # run() method
    SayouChunk(
        content="    def run(self, raw_data, strategy='auto', **kwargs):\n        normalizer_cls = self._resolve_normalizer(raw_data, strategy)\n        return normalizer_cls().normalize(raw_data, **kwargs)",
        metadata={
            "semantic_type": "method",
            "source": SOURCE_PATH,
            "language": "python",
            "parent_node": "RefineryPipeline",
            "function_name": "run",
            "calls": ["_resolve_normalizer"],
            "return_type": "List[SayouBlock]",
            "lineStart": 14,
            "lineEnd": 16,
        },
    ),
    # Top-level helper function
    SayouChunk(
        content="def _load_module(name: str) -> None:\n    importlib.import_module(name)",
        metadata={
            "semantic_type": "function",
            "source": SOURCE_PATH,
            "language": "python",
            "function_name": "_load_module",
            "params": [
                {
                    "name": "name",
                    "kind": "POSITIONAL_OR_KEYWORD",
                    "type_annotation": "str",
                }
            ],
            "calls": ["importlib.import_module"],
            "lineStart": 20,
            "lineEnd": 21,
        },
    ),
]
```

## Basic Conversion

Pass the chunk list with ``strategy="code_chunk"``.

The output contains:
- 1 × sayou:File node
- 1 × sayou:Class node (RefineryPipeline)
- 1 × sayou:AttributeBlock node
- 2 × sayou:Method nodes (__init__, run)
- 1 × sayou:Function node (_load_module)
- 1 × sayou:CodeBlock node (imports)

```python
output = pipeline.run(chunks, strategy="code_chunk")

print("=== Basic Conversion ===")
print(f"  Input chunks : {len(chunks)}")
print(f"  Output nodes : {len(output.nodes)}")
for node in output.nodes:
    cls = node.node_class.split(":")[-1]
    label = node.friendly_name or node.node_id.split("::")[-1]
    print(f"  [{cls:15s}] {label}")
```

## Node ID Convention

IDs are stable across refactors because they encode symbol names, not
line numbers.

```python
print("\n=== Node ID Convention ===")
for node in output.nodes:
    print(f"  {node.node_id}")
```

## Class Hierarchy (Pass 2)

After all nodes are built, class nodes receive ``sayou:contains`` edges
listing their children.  Child nodes carry ``sayou:hasParent`` back-links.

```python
from sayou.core.ontology import SayouClass, SayouPredicate

print("\n=== Class Hierarchy ===")
for node in output.nodes:
    if node.node_class == SayouClass.CLASS:
        children = node.relationships.get(SayouPredicate.CONTAINS, [])
        print(f"  {node.friendly_name} ({node.node_class})")
        for child_id in children:
            print(f"    sayou:contains → {child_id.split('::')[-1]}")

print()
for node in output.nodes:
    parent = node.relationships.get(SayouPredicate.HAS_PARENT, [])
    if parent:
        print(f"  {node.node_id.split('::')[-1]}")
        print(f"    sayou:hasParent → {parent[0].split('::')[-1]}")
```

## Call-graph Attributes

Raw call metadata is forwarded to node attributes so CodeGraphBuilder
can resolve them into typed CALLS / MAYBE_CALLS edges.

```python
from sayou.core.ontology import SayouAttribute

print("\n=== Call-graph Attributes ===")
for node in output.nodes:
    calls = node.attributes.get(SayouAttribute.CALLS_RAW, [])
    if calls:
        name = node.attributes.get(SayouAttribute.SYMBOL_NAME, node.node_id)
        print(f"  {name}  calls_raw={calls}")
```

## File Node

Each unique source path gets exactly one ``sayou:File`` node.
It carries the file path and language.

```python
print("\n=== File Node ===")
for node in output.nodes:
    if node.node_class == SayouClass.FILE:
        print(f"  node_id   : {node.node_id}")
        print(f"  file_path : {node.attributes.get(SayouAttribute.FILE_PATH)}")
        print(f"  language  : {node.attributes.get(SayouAttribute.LANGUAGE)}")
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
with open("code_chunk_nodes.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"\nSaved {len(output.nodes)} node(s) to 'code_chunk_nodes.json'")
```