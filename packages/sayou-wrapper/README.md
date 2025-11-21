# sayou-wrapper

[![Build Status](https://img.shields.io/github/actions/workflow/status/sayouzone/sayou-fabric/ci.yml?branch=main)](https://github.com/sayouzone/sayou-fabric/actions)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://sayouzone.github.io/sayou-fabric/library-guides/wrapper/)

`sayou-wrapper` is a schema normalization library that acts as the **"Gatekeeper"** of the Sayou Data Platform. It transforms heterogeneous data from various sources (Chunks, API responses, CSVs) into the unified **Sayou Standard Schema**.

This library ensures that downstream components like `sayou-assembler` do not need to understand the complexity of external data formats. If data passes through the Wrapper, it is guaranteed to be a valid `SayouNode`.

## Philosophy

**"Polymorphic Input, Monomorphic Output."**
Regardless of whether the input is a Markdown chunk, a Subway API JSON, or a Stock price list, the output must always be a list of standardized `SayouNode` objects. This abstraction allows the Knowledge Graph builder to remain agnostic to the data source.

## 🚀 Key Features

* **Standard Schema (`SayouNode`):** Defines the universal atom of the platform with `node_id`, `node_class`, `attributes`, and `relationships`.
* **Dynamic Adapter Pattern:** Uses a registry-based pipeline to automatically route inputs to the correct adapter (e.g., `DocumentChunkAdapter`).
* **Built-in Validation:** Leverages Pydantic to strictly validate data integrity upon creation.
* **Semantic Mapping:** Automatically converts `sayou-chunking` metadata (e.g., `semantic_type`) into Ontology classes (e.g., `sayou:Table`).

## 📦 Installation

```python
pip install sayou-wrapper
```

## ⚡ Quickstart

The `WrapperPipeline` orchestrates the adaptation process. You don't need to import specific adapters; just specify the `adapter_type`.

```python
import os
import json
from sayou.wrapper.pipeline import WrapperPipeline

def run_demo():
    # 1. Load Input (Output from sayou-chunking)
    input_file = "chunks_output.json"
    
    # 2. Initialize Pipeline
    # Use 'document_chunk' adapter to process chunking results
    pipeline = WrapperPipeline(adapter_type="document_chunk")
    pipeline.initialize()

    # 3. Run Transformation
    # The pipeline automatically loads the JSON file
    result = pipeline.run(input_file)
    
    # 4. Check Standard Nodes
    for node in result['nodes'][:2]:
        print(f"[ID] {node['node_id']}")
        print(f"[Class] {node['node_class']}")
        print(f"[Attrs] {node['attributes']}")
        print("-" * 20)

if __name__ == "__main__":
    run_demo()
```

## 🤝 Contributing

To support a new data source (e.g., Notion API), simply implement a new `BaseAdapter` plugin and register it with the pipeline.

## 📜 License

Apache 2.0 License © 2025 Sayouzone