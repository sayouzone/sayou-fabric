<div align='center'>

<img src="https://github.com/sayouzone/sayou-fabric/blob/main/docs/assets/sayou_logo.png?raw=true" width="250">

# Sayou Fabric

[![PyPI](https://img.shields.io/pypi/v/sayou-document.svg?color=blue&label=pypi%20package)](https://pypi.org/project/sayou-document/)
[![Docs](https://img.shields.io/badge/docs-mkdocs-success.svg?logo=materialformkdocs)](https://sayouzone.github.io/sayou-fabric/)
[![Python](https://img.shields.io/badge/python-3.8%2B-blueviolet.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-red.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Downloads](https://static.pepy.tech/badge/sayou-document?)](https://pepy.tech/project/sayou-document)
[![GitHub stars](https://img.shields.io/github/stars/sayouzone/sayou-fabric.svg)](https://github.com/sayouzone/sayou-fabric/stargazers)

_The Data-Centric Framework for Building Enterprise RAG Pipelines_

</div>

[한국어 (README.ko.md)](./README.ko.md)

---

## 1. Philosophy: Why Sayou Fabric?

**Sayou Fabric** operates on a simple premise: **"The quality of your RAG depends on the structure of your data, not just the model."**

While other frameworks focus on chaining LLMs, Sayou Fabric focuses on the **Data Lifecycle**. It decomposes the complex RAG pipeline into **10 atomic stages**, ensuring that raw data is meticulously cleaned, structured, and assembled into a Knowledge Graph before it ever touches an LLM.

### 1.1. Structure-First Architecture
We don't just split text; we understand it. By preserving document hierarchy (headers, tables, code blocks) and enforcing strict schemas, we eliminate context loss and hallucination at the source.

### 1.2. The 3-Tier Design Pattern
Every library in the ecosystem follows a consistent **Interface-Template-Plugin** pattern, guaranteeing both stability and infinite extensibility.
* **Tier 1 (Interface):** The immutable contract.
* **Tier 2 (Template):** Batteries-included standard logic.
* **Tier 3 (Plugin):** Vendor-specific or custom logic extensions.

---

## 2. The Ecosystem

Sayou Fabric consists of independent, loosely coupled libraries that work together seamlessly.

| Package | Version | Description |
| :--- | :--- | :--- |
| `sayou-core` | [![PyPI version](https://img.shields.io/pypi/v/sayou-core.svg?color=blue)](https://pypi.org/project/sayou-core/) | Base components, logging, and decorators. |
| `sayou-connector` | [![PyPI version](https://img.shields.io/pypi/v/sayou-connector.svg?color=blue)](https://pypi.org/project/sayou-connector/) | Fetches raw data from Files, Web, APIs, or DBs via smart generators. |
| `sayou-document` | [![PyPI version](https://img.shields.io/pypi/v/sayou-document.svg?color=blue)](https://pypi.org/project/sayou-document/) | High-fidelity parsing of PDF, DOCX, PPTX (preserves coords & styles). |
| `sayou-refinery` | [![PyPI version](https://img.shields.io/pypi/v/sayou-refinery.svg?color=blue)](https://pypi.org/project/sayou-refinery/) | Normalizes complex JSON structures into clean, standard Markdown. |
| `sayou-chunking` | [![PyPI version](https://img.shields.io/pypi/v/sayou-chunking.svg?color=blue)](https://pypi.org/project/sayou-chunking/) | Context-aware chunking. Protects atomic blocks (tables/code). |
| `sayou-wrapper` | [![PyPI version](https://img.shields.io/pypi/v/sayou-wrapper.svg?color=blue)](https://pypi.org/project/sayou-wrapper/) | Enforces the company schema (`SayouNode`) on all incoming data. |
| `sayou-assembler` | [![PyPI version](https://img.shields.io/pypi/v/sayou-assembler.svg?color=blue)](https://pypi.org/project/sayou-assembler/) | Assembles nodes into an In-Memory Knowledge Graph (Parent-Child linking). |
| `sayou-loader` | [![PyPI version](https://img.shields.io/pypi/v/sayou-loader.svg?color=blue)](https://pypi.org/project/sayou-loader/) | Saves the constructed graph to File, VectorDB, or GraphDB with fallback safety. |
| `sayou-extractor` | [![PyPI version](https://img.shields.io/pypi/v/sayou-extractor.svg?color=blue)](https://pypi.org/project/sayou-extractor/) | Intelligent retrieval using Hybrid Search (Vector + Graph). |
| `sayou-llm` | [![PyPI version](https://img.shields.io/pypi/v/sayou-llm.svg?color=blue)](https://pypi.org/project/sayou-llm/) | An adapter layer for various LLMs (OpenAI, Anthropic, Local). |
| `sayou-brain` | [![PyPI version](https://img.shields.io/pypi/v/sayou-brain.svg?color=blue)](https://pypi.org/project/sayou-brain/) | The control tower that manages the entire pipeline (`StandardPipeline`). |

---

## 3. Installation

You can install the entire suite via the orchestrator package:

```bash
pip install sayou-brain
```

Or install individual components as needed:

```bash
pip install sayou-chunking sayou-document
```

---

## 4. Quick Start

The `StandardPipeline` in `sayou-brain` acts as a Facade, abstracting away the complexity of the underlying modules. It intelligently routes data based on file types (PDF, Markdown, JSON, etc.).

### Step 1: Install & Initialize

```python
from sayou.brain.pipelines.standard import StandardPipeline

# Initialize the orchestrator (automatically loads all sub-pipelines)
# You can pass a config dict here for customization (e.g., chunk_size, PII masking)
brain = StandardPipeline()
brain.initialize()
```

### Step 2: Ingest Data (ETL)

Just point to a file or a URL. The brain handles **Connecting -> Parsing -> Refining -> Chunking -> Wrapping -> Assembling -> Loading**.

```python
# Example: Ingest a PDF file or a folder
# This creates a Knowledge Graph structure and saves it to 'knowledge_graph.json'
result = brain.ingest(
    source="./reports/financial_q1.pdf",
    destination="knowledge_graph.json",
    strategies={
        "connector": "local_scan", # How to fetch
        "chunking": "markdown",    # How to split (if applicable)
        "assembler": "graph",      # How to build structure
        "loader": "file"           # Where to save
    }
)

print(f"Ingestion Complete. Processed: {result['processed']}")
```

### Step 3: Check Result

The output is a structured JSON ready for Graph Databases or Vector Stores.

```json
{
  "nodes": [
    {
      "node_id": "sayou:doc:1_h_0",
      "node_class": "sayou:Topic",
      "attributes": { "schema:text": "Financial Summary Q1" },
      "relationships": {}
    },
    ...
  ],
  "edges": [...]
}
```

## 5. Documentation

For detailed architecture guides, API references, and advanced tutorials (e.g., Creating Custom Plugins), please visit our **[Official Documentation](https://sayouzone.github.io/sayou-fabric/)**.

* [Architecture Guide](https://sayouzone.github.io/sayou-fabric/architecture)
* [Plugin Development](https://sayouzone.github.io/sayou-fabric/guides/plugins)
* [API Reference](https://sayouzone.github.io/sayou-fabric/api)

---

## 6. Contributing

We welcome contributions!
Sayou Fabric is designed to be modular. You can contribute by:
1.  Adding a new **Connector Plugin** (e.g., Notion, Slack).
2.  Improving **Document Parsers** (e.g., HWP support).
3.  Enhancing **Assembler Strategies** (e.g., Semantic linking).

Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting a Pull Request.

---

## 7. License

Apache 2.0 License © 2025 **Sayouzone**