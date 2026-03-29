!!! abstract "Source"
    Synced from [`packages/sayou-assembler/examples/quick_start_graph.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-assembler/examples/quick_start_graph.py).

## Setup

Assemble SayouNodes into a graph structure (nodes + edges) using
`AssemblerPipeline` with `GraphBuilder`.

`GraphBuilder` accepts a `SayouOutput` from `WrapperPipeline` and produces
a flat `{"nodes": [...], "edges": [...]}` dict suitable for:
- Loading into graph databases (Neo4j, NetworkX)
- Visualising document hierarchies
- Feeding into `LoaderPipeline` downstream

Key features:
- Converts node relationships into typed edges
- Automatically adds reverse edges (e.g. hasParent → hasChild)
- Preserves all node attributes (excluding relationship fields)

```python
import json

from sayou.core.schemas import SayouNode, SayouOutput

from sayou.assembler.builder.graph_builder import GraphBuilder
from sayou.assembler.pipeline import AssemblerPipeline

pipeline = AssemblerPipeline(extra_builders=[GraphBuilder])
```

## Basic Graph Assembly

Pass a `SayouOutput` (the output of WrapperPipeline) with
``strategy="GraphBuilder"``.

Returns a dict with:
- ``nodes``  — list of node dicts (attributes flattened, relationships excluded)
- ``edges``  — list of edge dicts with source, target, type, is_reverse
- ``stats``  — node_count, edge_count
- ``metadata`` — forwarded from the input SayouOutput

```python
nodes = [
    SayouNode(
        node_id="sayou:doc:overview_pdf:c001",
        node_class="sayou:Topic",
        friendly_name="Architecture",
        attributes={"sayou:text": "Architecture overview", "sayou:pageIndex": 1},
        relationships={},
    ),
    SayouNode(
        node_id="sayou:doc:overview_pdf:c002",
        node_class="sayou:Text",
        friendly_name="Para 1",
        attributes={
            "sayou:text": "Sayou Fabric consists of eight libraries.",
            "sayou:pageIndex": 1,
        },
        relationships={"sayou:hasParent": ["sayou:doc:overview_pdf:c001"]},
    ),
    SayouNode(
        node_id="sayou:doc:overview_pdf:c003",
        node_class="sayou:Text",
        friendly_name="Para 2",
        attributes={
            "sayou:text": "Each library handles one pipeline stage.",
            "sayou:pageIndex": 1,
        },
        relationships={"sayou:hasParent": ["sayou:doc:overview_pdf:c001"]},
    ),
]

output = SayouOutput(nodes=nodes, metadata={"source": "overview.pdf"})
result = pipeline.run(output, strategy="GraphBuilder")

print("=== Basic Graph Assembly ===")
print(f"  Nodes : {result['stats']['node_count']}")
print(f"  Edges : {result['stats']['edge_count']}")
for e in result["edges"]:
    direction = "←" if e["is_reverse"] else "→"
    print(
        f"  {e['source'].split(':')[-1]:10s} {direction} [{e['type'].split(':')[-1]:10s}] {e['target'].split(':')[-1]}"
    )
```

## Bi-directional Edges

`GraphBuilder` automatically generates a reverse edge for each forward edge.

| Forward predicate   | Reverse predicate    |
|---------------------|----------------------|
| sayou:hasParent     | sayou:hasChild       |
| sayou:belongsTo     | sayou:contains       |
| sayou:next          | sayou:previous       |
| (other)             | (other)_REV          |

This enables traversal in both directions without storing duplicate data
in the source nodes.

```python
print("\n=== Bi-directional Edges ===")
for e in result["edges"]:
    tag = "REVERSE" if e["is_reverse"] else "forward"
    print(
        f"  [{tag:7s}] {e['type']:22s}  {e['source'].split(':')[-1]} → {e['target'].split(':')[-1]}"
    )
```

## Node Properties

Node dicts in the output contain all attributes from the original SayouNode.
The `relationships` field is excluded (moved to edges).

```python
print("\n=== Node Properties ===")
for n in result["nodes"]:
    print(
        f"  {n['node_id'].split(':')[-1]:10s}  class={n['node_class'].split(':')[-1]:8s}  "
        f"text={str(n.get('sayou:text', ''))[:30]!r}"
    )
```

## Chaining with WrapperPipeline

In a real pipeline, WrapperPipeline output flows directly into
AssemblerPipeline — no manual node construction needed.

    wrapper_output = WrapperPipeline.process(chunks, strategy="document_chunk",
                                              extra_adapters=[DocumentChunkAdapter])
    graph = AssemblerPipeline.process(wrapper_output, strategy="GraphBuilder",
                                       extra_builders=[GraphBuilder])

## Save Results

```python
with open("graph_output.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False, default=str)

print(
    f"\nSaved graph ({result['stats']['node_count']} nodes, "
    f"{result['stats']['edge_count']} edges) to 'graph_output.json'"
)
```