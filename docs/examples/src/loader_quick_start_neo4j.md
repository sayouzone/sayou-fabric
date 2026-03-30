!!! abstract "Source"
    Synced from [`packages/sayou-loader/examples/quick_start_neo4j.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-loader/examples/quick_start_neo4j.py).

## Setup

Load a knowledge graph into Neo4j using `LoaderPipeline` with
`Neo4jWriter`.

`Neo4jWriter` provides high-performance graph loading:

- Groups nodes by label for UNWIND-based batch MERGE
- Handles relationships separately via typed MATCH … MERGE
- Sanitises properties: dicts/lists → JSON strings for compatibility
- Supports URI authentication and explicit ``(user, password)`` tuples

URI pattern: ``bolt://host:port`` or ``neo4j://host:port``

Install the driver:

    pip install neo4j

```python
import json
from unittest.mock import MagicMock, patch

from sayou.core.schemas import SayouNode, SayouOutput

from sayou.loader.pipeline import LoaderPipeline
from sayou.loader.plugins.neo4j_writer import Neo4jWriter

pipeline = LoaderPipeline(extra_writers=[Neo4jWriter])
```

## Sample Graph Data

`Neo4jWriter` accepts:
- A list of plain dicts (output of GraphBuilder or CypherBuilder prep)
- SayouNode objects (converted automatically)

Each dict may have a ``links`` key for relationships:

    {"id": "n1", "label": "Person", "name": "Alice",
     "links": [{"target": "n2", "type": "KNOWS"}]}

```python
graph_data = [
    {
        "id": "sayou:doc:report_pdf:c001",
        "label": "Topic",
        "friendly_name": "Executive Summary",
        "sayou:text": "Key findings of the quarterly report.",
        "sayou:pageIndex": 1,
        "links": [],
    },
    {
        "id": "sayou:doc:report_pdf:c002",
        "label": "Text",
        "friendly_name": "Finding 1",
        "sayou:text": "Revenue grew 23% year-over-year.",
        "sayou:pageIndex": 1,
        "links": [{"target": "sayou:doc:report_pdf:c001", "type": "HAS_PARENT"}],
    },
    {
        "id": "sayou:doc:report_pdf:c003",
        "label": "Table",
        "friendly_name": "Revenue Table",
        "sayou:text": "Q1: 1.2M | Q2: 1.5M | Q3: 1.8M",
        "sayou:pageIndex": 2,
        "links": [{"target": "sayou:doc:report_pdf:c001", "type": "HAS_PARENT"}],
    },
]
```

## Write to Neo4j (mocked)

The writer connects, groups nodes by label, then executes batch MERGE
queries using UNWIND for efficiency.

```python
print("=== Write to Neo4j (mocked) ===")

mock_gdb = MagicMock()
mock_session = MagicMock()
mock_gdb.return_value.session.return_value.__enter__ = lambda s: mock_session
mock_gdb.return_value.session.return_value.__exit__ = MagicMock(return_value=False)

with patch("sayou.loader.plugins.neo4j_writer.GraphDatabase", mock_gdb):
    result = pipeline.run(
        graph_data,
        "bolt://localhost:7687",
        strategy="Neo4jWriter",
        auth=("neo4j", "password"),
        id_key="id",
    )

print(f"  Result              : {result}")
print(f"  session.execute_write calls: {mock_session.execute_write.call_count}")
```

## UNWIND Batch Merge

Nodes are grouped by ``label`` and merged in a single Cypher statement:

    UNWIND $batch AS row
    MERGE (n:`Topic` { `id`: row.`id` })
    SET n += row

This is significantly faster than one MERGE per node for large graphs.

```python
print("\n=== Node Grouping by Label ===")
import logging
from collections import defaultdict

from sayou.loader.plugins.neo4j_writer import Neo4jWriter

nw = Neo4jWriter()
nw.logger = logging.getLogger("test")
nw._callbacks = []

normalised = nw._normalize_input_data(graph_data)
by_label = defaultdict(list)
for node in normalised:
    by_label[node.get("label", "Entity")].append(node["id"])

for label, ids in by_label.items():
    print(f"  :{label:10s}  {len(ids)} node(s): {ids}")
```

## Property Sanitisation

Neo4j property values must be primitives or lists of primitives.
`Neo4jWriter._sanitize_props` converts complex values:

- ``list[dict]``  → JSON string
- ``dict``        → JSON string
- ``list[str/int]`` → preserved as-is
- ``links``       → excluded (converted to relationships)

```python
print("\n=== Property Sanitisation ===")
raw = {
    "id": "n1",
    "name": "Alice",
    "tags": ["python", "llm"],  # primitive list → kept
    "meta": {"source": "pdf"},  # dict → JSON string
    "links": [{"target": "n2"}],  # excluded
}
sanitised = nw._sanitize_props(raw)
for k, v in sanitised.items():
    print(f"  {k:8s}: {v!r}  ({type(v).__name__})")
```

## Real Connection (commented — requires running Neo4j)

result = pipeline.run(
        graph_data,
        "bolt://localhost:7687",
        strategy="Neo4jWriter",
        auth=("neo4j", "password"),
    )

Or with Neo4j AuraDB:

    result = pipeline.run(
        graph_data,
        "neo4j+s://xxxxxxxx.databases.neo4j.io",
        strategy="Neo4jWriter",
        auth=("neo4j", "<AuraDB-password>"),
    )

```python
print("\nNeo4jWriter example complete.")
```

## Save Results

Save the generated Cypher queries to a file for inspection or manual
execution.  Use `LoaderPipeline` with `FileWriter` to persist any other
graph payload format.

```python
import json

cypher_queries = [
    f"MERGE (n:`{node['label']}` {{id: '{node['id']}'}}) SET n += {json.dumps({k: v for k, v in node.items() if k not in ('label', 'links')}, ensure_ascii=False)}"
    for node in graph_data
]

with open("neo4j_queries.cypher", "w", encoding="utf-8") as f:
    f.write("\n\n".join(cypher_queries))

print(f"Saved {len(cypher_queries)} Cypher query/queries to 'neo4j_queries.cypher'")
```