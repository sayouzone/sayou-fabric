# Library Guide: sayou-assembler

`sayou-assembler` acts as the **architect** of the Knowledge Graph. It receives a bag of loose nodes from the Wrapper and creates a structured, interconnected network.

It sits right before `sayou-loader`. While the Loader's job is I/O (writing to DB), the Assembler's job is Logic (defining topology).

---

## 1. Core Concepts & Architecture

The library uses a **Dynamic Strategy Pattern** to allow different ways of building graphs.

### Tier 1: Interfaces
* **`BaseBuilder`**: The interface for all assembly strategies. It accepts `WrapperOutput` and returns a dictionary representation of the `KnowledgeGraph`.

### Tier 2: Builders (Strategies)
* **`HierarchyBuilder`**: The default strategy.
    * Iterates through all nodes.
    * Connects nodes based on the `relationships` dictionary (e.g., `sayou:hasParent`).
    * **Auto-Reverse Linking**: Automatically creates reverse edges (e.g., `sayou:hasChild`) to allow top-down traversal in RAG.

### Core Model: `KnowledgeGraph`
An agnostic, in-memory representation of the graph.

```python
class KnowledgeGraph:
    nodes: Dict[str, GraphNode]
    edges: List[GraphEdge]
    
    def to_dict(self): ...
```

---

## 2. Usage Examples

### 2.1. Building a Document Hierarchy Graph

This is the standard use case for RAG pipelines where document structure (Header -> Body) is preserved.

```python
from sayou.assembler.pipeline import AssemblerPipeline

pipeline = AssemblerPipeline(strategy="hierarchy")

# Input must follow the Sayou Standard Schema
graph_dict = pipeline.run(wrapper_output_data)
```

### 2.2. Adding Custom Strategies (Tier 3)

You can implement complex logic, such as linking nodes that share the same keywords.

```python
from sayou.assembler.interfaces.base_builder import BaseBuilder

class SemanticBuilder(BaseBuilder):
    component_name = "SemanticBuilder"
    SUPPORTED_TYPES = ["semantic"]

    def _do_assemble(self, data):
        # Custom logic to link nodes by similarity...
        return kg.to_dict()
```

---

## 3. Logic Deep Dive: Automatic Linking

The `HierarchyBuilder` performs intelligent linking to ensure the graph is traversable in both directions.

**Input Node:**

```
Node A: { id: "child_1", relations: { "hasParent": ["parent_1"] } }
```

**Assembled Graph:**

```
1. Edge Created: child_1 --[hasParent]--> parent_1
2. Reverse Logic Triggered (internal helper)
3. Edge Created: parent_1 --[hasChild]--> child_1
```

This ensures that when a user searches for the "Parent Topic," the system can easily find all "Child Contents."