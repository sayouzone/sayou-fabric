!!! abstract "Source"
    Synced from [`packages/sayou-assembler/examples/quick_start_cypher.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-assembler/examples/quick_start_cypher.py).

## Setup

Generate Neo4j Cypher queries from SayouNodes using `AssemblerPipeline`
with `CypherBuilder`.

`CypherBuilder` converts each SayouNode into a ``MERGE`` statement and
each relationship into a ``MATCH … MERGE`` relationship statement.

All queries use ``MERGE`` (idempotent upsert) so re-running the same
pipeline on updated data is safe — existing nodes are updated, not
duplicated.

Use `LoaderPipeline` with `Neo4jWriter` for automatic execution.
`CypherBuilder` is useful when you need to inspect, log, or batch the
queries before sending them to the database.

Install dependencies:

    pip install neo4j    # only needed to actually run queries

```python
import json

from sayou.core.schemas import SayouNode, SayouOutput

from sayou.assembler.pipeline import AssemblerPipeline
from sayou.assembler.plugins.cypher_builder import CypherBuilder

pipeline = AssemblerPipeline(extra_builders=[CypherBuilder])
```

## Generate Cypher Queries

Pass a `SayouOutput` with ``strategy="CypherBuilder"``.

Returns a ``List[str]`` — one Cypher statement per node or relationship.

Query types:
- Node:         ``MERGE (n:`Label` {id: '…'}) SET n += {props}``
- Relationship: ``MATCH (a {id: '…'}), (b {id: '…'}) MERGE (a)-[:`REL`]->(b)``

```python
nodes = [
    SayouNode(
        node_id="sayou:doc:report_pdf:c001",
        node_class="sayou:Topic",
        friendly_name="Executive Summary",
        attributes={
            "sayou:text": "Key findings of the quarterly report.",
            "sayou:pageIndex": 1,
            "sayou:source": "report.pdf",
        },
        relationships={},
    ),
    SayouNode(
        node_id="sayou:doc:report_pdf:c002",
        node_class="sayou:Text",
        friendly_name="Finding 1",
        attributes={
            "sayou:text": "Revenue grew 23% year-over-year.",
            "sayou:pageIndex": 1,
        },
        relationships={"sayou:hasParent": ["sayou:doc:report_pdf:c001"]},
    ),
    SayouNode(
        node_id="sayou:doc:report_pdf:c003",
        node_class="sayou:Table",
        friendly_name="Revenue Table",
        attributes={
            "sayou:text": "Q1: 1.2M | Q2: 1.5M | Q3: 1.8M",
            "sayou:pageIndex": 2,
        },
        relationships={"sayou:hasParent": ["sayou:doc:report_pdf:c001"]},
    ),
]

output = SayouOutput(nodes=nodes, metadata={"source": "report.pdf"})
queries = pipeline.run(output, strategy="CypherBuilder")

print("=== Generate Cypher Queries ===")
print(f"  Total queries: {len(queries)}")
print()
for i, q in enumerate(queries, 1):
    print(f"  [{i}] {q[:80]}{'…' if len(q) > 80 else ''}")
```

## MERGE Semantics

Each node query is:

    MERGE (n:`sayou_Topic` {id: 'sayou:doc:…'}) SET n += { … }

- If the node already exists, its properties are updated.
- If it does not exist, it is created.
- Colons in label names are replaced with underscores (Cypher syntax).

```python
merge_queries = [q for q in queries if q.startswith("MERGE")]
match_queries = [q for q in queries if q.startswith("MATCH")]

print("\n=== MERGE Semantics ===")
print(f"  Node MERGE queries        : {len(merge_queries)}")
print(f"  Relationship MATCH queries: {len(match_queries)}")
print()
print("  First node query:")
print(f"    {merge_queries[0][:120]}")
```

## Relationship Queries

Each relationship in a node's `relationships` dict becomes:

    MATCH (a {id: '<source>'}), (b {id: '<target>'})
    MERGE (a)-[:`<REL_TYPE>`]->(b)

Relationship type colons are also replaced: ``sayou:hasParent`` →
``sayou_hasParent``.

```python
print("\n=== Relationship Queries ===")
for q in match_queries:
    print(f"  {q}")
```

## Execute Queries (commented — requires Neo4j)

To execute the generated queries against a running Neo4j instance:

    from neo4j import GraphDatabase
    driver = GraphDatabase.driver("bolt://localhost:7687",
                                  auth=("neo4j", "password"))
    with driver.session() as session:
        for query in queries:
            session.run(query)
    driver.close()

For high-volume loads, prefer LoaderPipeline + Neo4jWriter which uses
UNWIND batching for better performance.

## Save Queries

```python
with open("cypher_queries.cypher", "w", encoding="utf-8") as f:
    f.write("\n\n".join(queries))

print(f"\nSaved {len(queries)} Cypher query/queries to 'cypher_queries.cypher'")
```