# Library Guide: sayou-loader

`sayou-loader` manages the **egress** of data from the pipeline. It connects the ephemeral processing world (Memory) to the persistent storage world (Disk/DB).

It is designed to be the final, reliable step in the `sayou-rag` ingestion process.

---

## 1. Core Concepts & Architecture

The library follows the standard **3-Tier Architecture** with a focus on fail-safety.

### Tier 1: Interfaces
* **`BaseLoader`**: The abstract base class. It employs the **Template Method Pattern**, implementing standardized logging and error handling in the `load()` method while delegating actual logic to `_do_load()`.

### Tier 2: Templates (The Defaults)
* **`FileLoader`**: The workhorse. It saves data to the local filesystem. It intelligently handles different data types:
    * `Dict/List` -> JSON file
    * `Bytes` -> Binary file
    * `String` -> Text file
    * `Other` -> Pickle file

### Orchestrator: Pipeline & Fallback
The `LoaderPipeline` contains critical logic: **Smart Fallback**.

    if handler_not_found:
        log_warning("Fallback to FileLoader")
        handler = FileLoader()

This ensures that long-running pipeline jobs do not end in data loss due to a misconfiguration or network issue at the very last step.

---

## 2. Usage Examples

### 2.1. Saving Knowledge Graphs (Standard RAG)

In a typical `sayou-rag` workflow, the Assembler outputs a dictionary representing the graph.

```python
loader.run(
    data=kg_graph_dict, 
    destination="data/kg_v1.json", 
    target_type="file"
)
```

### 2.2. Integrating with Graph Databases (Tier 3)

You can extend `sayou-loader` to write directly to databases like Neo4j.

```python
# (Requires sayou-loader[neo4j] or custom plugin)
loader.run(
    data=kg_graph_dict,
    destination="bolt://neo4j:password@localhost:7687",
    target_type="neo4j"
)
```

---

## 3. Creating Custom Loaders (Tier 3)

To support a new storage backend (e.g., AWS S3), simply inherit from `BaseLoader`.

```python
from sayou.loader.interfaces.base_loader import BaseLoader

class S3Loader(BaseLoader):
    component_name = "S3Loader"
    SUPPORTED_TYPES = ["s3"]

    def _do_load(self, data, destination, **kwargs):
        # Logic to upload data to S3 bucket (destination)
        s3_client.put_object(...)
        return True
```

Register this loader with the pipeline using the `extra_loaders` argument during initialization.