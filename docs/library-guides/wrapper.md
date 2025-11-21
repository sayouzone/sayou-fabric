# Library Guide: sayou-wrapper

`sayou-wrapper` serves as the **standardization layer** in the data pipeline. Its primary role is to decouple the "Data Source" (Upstream) from the "Data Consumer" (Downstream).

By enforcing a strict schema (`SayouNode`), it allows `sayou-assembler` and `sayou-loader` to operate purely on graph logic without worrying about field naming conventions or data inconsistencies.

---

## 1. Core Concepts & Architecture

The library follows the **3-Tier Architecture** with a **Dynamic Registry Pattern**.

### Tier 1: Interfaces (The Contract)
* **`BaseAdapter`**: The abstract base class. It defines the `adapt()` method which takes `Any` input and returns a `WrapperOutput` (Pydantic Model).

### Tier 2: Adapters (The Implementations)
* **`DocumentChunkAdapter`**: The default adapter designed to process the output of `sayou-chunking`.
    * Maps `chunk_id` to `sayou:doc:{id}`.
    * Maps `semantic_type="table"` to `sayou:Table` class.
    * Preserves `parent_id` for graph lineage.

### Core Schema: `SayouNode`
This is the lingua franca of the platform.

```python
class SayouNode(BaseModel):
    node_id: str       # Unique URI
    node_class: str    # Ontology Class
    attributes: Dict   # Dynamic Properties
    relationships: Dict[str, List[str]] # Edges
```

---

## 2. Usage Examples

### 2.1. Processing Document Chunks

When building a RAG pipeline from documents, `sayou-wrapper` bridges the gap between text chunks and graph nodes.

```python
from sayou.wrapper.pipeline import WrapperPipeline

pipeline = WrapperPipeline(adapter_type="document_chunk")

# Input can be a file path or a list of dicts
nodes = pipeline.run("chunks.json")
```

### 2.2. Extending for Custom Data (Tier 3)

You can create custom adapters for structured data like APIs.

```python
from sayou.wrapper.interfaces.base_adapter import BaseAdapter
from sayou.wrapper.schemas.sayou_standard import WrapperOutput, SayouNode

class MyApiAdapter(BaseAdapter):
    component_name = "MyApiAdapter"
    SUPPORTED_TYPES = ["my_api"]

    def _do_adapt(self, raw_data):
        # Implementation logic...
        return WrapperOutput(nodes=[...])
```

---

## 3. Data Flow

**Input (from Chunking):**

```json
{
    "chunk_content": "...",
    "metadata": { "semantic_type": "h1", "chunk_id": "123" }
}
```

**Output (Standard Node):**

```json
{
    "node_id": "sayou:doc:123",
    "node_class": "sayou:Topic",
    "attributes": {
        "schema:text": "...",
        "sayou:semanticType": "h1"
    },
    "relationships": {}
}
```