# sayou-assembler

[![Build Status](https://img.shields.io/github/actions/workflow/status/sayouzone/sayou-fabric/ci.yml?branch=main)](https://github.com/sayouzone/sayou-fabric/actions)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://sayouzone.github.io/sayou-fabric/library-guides/assembler/)

`sayou-assembler` is the graph construction engine of the Sayou Data Platform. It takes standardized nodes from `sayou-wrapper` and assembles them into a logical **In-Memory Knowledge Graph**.

It is responsible for interpreting relationships (like Parent-Child), generating reverse edges, and ensuring the graph's topological integrity before it is persisted by `sayou-loader`.

## Philosophy

**"Structure before Storage."**
A database is just a container. The value of a Knowledge Graph comes from its structure. `sayou-assembler` focuses on the logic of *connecting* dots (Nodes) to create meaning (Context), independent of the underlying database technology (Neo4j, SQL, NetworkX).

## 🚀 Key Features

* **In-Memory Graph Model:** Manages `GraphNode` and `GraphEdge` objects efficiently in Python.
* **Hierarchy Strategy:** Automatically builds tree-like structures using `parent_id` attributes.
* **Bi-directional Linking:** Automatically generates reverse edges (e.g., `hasChild` from `hasParent`) to enable bidirectional graph traversal.
* **Strategy Pattern:** Supports pluggable assembly strategies (Hierarchy, Semantic, Chronological).

## 📦 Installation

```python
pip install sayou-assembler
```

## ⚡ Quickstart

The `AssemblerPipeline` creates the graph using a specified strategy (default: `hierarchy`).

```python
import json
from sayou.assembler.pipeline import AssemblerPipeline

def run_demo():
    # 1. Load Standard Nodes (Output from sayou-wrapper)
    input_file = "wrapped_nodes.json"
    with open(input_file, "r", encoding="utf-8") as f:
        wrapper_output = json.load(f)

    # 2. Initialize Pipeline
    # Uses 'HierarchyBuilder' to link parent-child nodes
    pipeline = AssemblerPipeline(strategy="hierarchy")
    pipeline.initialize()

    # 3. Run Assembly
    kg_result = pipeline.run(wrapper_output)

    # 4. Inspect Graph
    print(f"Nodes: {kg_result['summary']['node_count']}")
    print(f"Edges: {kg_result['summary']['edge_count']}")
    
    for edge in kg_result['edges'][:3]:
        print(f"{edge['source']} --[{edge['type']}]--> {edge['target']}")

if __name__ == "__main__":
    run_demo()
```

## 🤝 Contributing

Contributions for new assembly strategies (e.g., constructing graphs based on keyword co-occurrence) are welcome.

## 📜 License

Apache 2.0 License © 2025 Sayouzone