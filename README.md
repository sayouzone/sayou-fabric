<div align='center'>

<img src="https://github.com/sayouzone/sayou-fabric/blob/main/docs/assets/sayou_logo.png?raw=true" width="250">

# Sayou Fabric

[![PyPI](https://img.shields.io/pypi/v/sayou-brain.svg?color=blue&label=pypi%20package)](https://pypi.org/project/sayou-brain/)
[![Docs](https://img.shields.io/badge/docs-mkdocs-success.svg?logo=materialformkdocs)](https://sayouzone.github.io/sayou-fabric/)
[![Python](https://img.shields.io/badge/python-3.8%2B-blueviolet.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-red.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Downloads](https://static.pepy.tech/badge/sayou-rag?color=orange)](https://pepy.tech/project/sayou-rag)
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

| Stage | Package | Description |
| :--- | :--- | :--- |
| **0. Core** | `sayou-core` | Base components, logging, and decorators. |
| **1. Ingest** | `sayou-connector` | Fetches raw data from Files, Web, APIs, or DBs via smart generators. |
| **2. Parse** | `sayou-document` | High-fidelity parsing of PDF, DOCX, PPTX (preserves coords & styles). |
| **3. Refine** | `sayou-refinery` | Normalizes complex JSON structures into clean, standard Markdown. |
| **4. Split** | `sayou-chunking` | Context-aware chunking. Protects atomic blocks (tables/code). |
| **5. Wrap** | `sayou-wrapper` | Enforces the company schema (`SayouNode`) on all incoming data. |
| **6. Build** | `sayou-assembler` | Assembles nodes into an In-Memory Knowledge Graph (Parent-Child linking). |
| **7. Load** | `sayou-loader` | Saves the constructed graph to File, VectorDB, or GraphDB with fallback safety. |
| **8. Query** | `sayou-extractor` | Intelligent retrieval using Hybrid Search (Vector + Graph). |
| **9. Gen** | `sayou-llm` | An adapter layer for various LLMs (OpenAI, Anthropic, Local). |
| **10. Main** | `sayou-brain` | The control tower that manages the entire pipeline (`StandardPipeline`). |

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

The `StandardPipeline` in `sayou-brain` acts as a Facade, abstracting away the complexity of the underlying modules. It automatically routes data based on input type.

### Step 1: Initialize the Brain

```python
from sayou.brain.pipeline.standard import StandardPipeline

# Initialize the orchestrator (automatically loads all sub-pipelines)
brain = StandardPipeline()
brain.initialize()
```

### Step 2: Ingest Data (ETL)

Just point to a file or a URL. The brain handles **Connecting -> Parsing -> Refining -> Chunking -> Wrapping -> Assembling -> Loading**.

```python
# Example: Ingest a PDF file
# This creates a Knowledge Graph and saves it to 'knowledge_graph.json'
result = brain.ingest(
    source="./reports/financial_q1.pdf",
    strategy="local_scan",
    save_to="knowledge_graph.json"
)

print(f"Ingestion Complete: {result['status']}")
print(f"Total Nodes Created: {result['total_nodes']}")
```

### Step 3: Ask Questions (Inference)

Query the structured knowledge you just created.

```python
# Ask a question based on the ingested knowledge graph
answer = brain.ask(
    query="What is the net profit for Q1?",
    load_from="knowledge_graph.json"
)

print(f"Answer: {answer}")
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