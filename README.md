<div align='center'>

<img src="https://github.com/sayouzone/sayou-fabric/blob/main/docs/assets/sayou_logo.png?raw=true" width="250">

# Sayou Fabric

[![PyPI](https://img.shields.io/pypi/v/sayou-connector.svg?color=blue&label=pypi%20package)](https://pypi.org/project/sayou-connector/)
[![Docs](https://img.shields.io/badge/docs-mkdocs-success.svg?logo=materialformkdocs)](https://sayouzone.github.io/sayou-fabric/)
[![Python](https://img.shields.io/badge/python-3.11%2B-blueviolet.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-red.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Downloads](https://static.pepy.tech/badge/sayou-connector)](https://pepy.tech/project/sayou-connector)
<!-- [![GitHub stars](https://img.shields.io/github/stars/sayouzone/sayou-fabric.svg)](https://github.com/sayouzone/sayou-fabric/stargazers) -->

_The Data-Centric Framework for Building Enterprise RAG Pipelines_
<br>
_**Observe, Structure, and Assemble your Knowledge Graph.**_

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
| `sayou-core` | [![PyPI](https://img.shields.io/pypi/v/sayou-core.svg?color=blue)](https://pypi.org/project/sayou-core/) | Base components, interfaces, and decorators. |
| `sayou-brain` | [![PyPI](https://img.shields.io/pypi/v/sayou-brain.svg?color=blue)](https://pypi.org/project/sayou-brain/) | **[Control Tower]** Orchestrates the entire pipeline (`StandardPipeline`). |
| `sayou-connector` | [![PyPI](https://img.shields.io/pypi/v/sayou-connector.svg?color=blue)](https://pypi.org/project/sayou-connector/) | **[Smart Fetcher]** Auto-detects sources (Notion, PDF, Web) via Scoring. |
| `sayou-document` | [![PyPI](https://img.shields.io/pypi/v/sayou-document.svg?color=blue)](https://pypi.org/project/sayou-document/) | **[High-Fidelity Parser]** Preserves layout, coordinates, and styles. |
| `sayou-refinery` | [![PyPI](https://img.shields.io/pypi/v/sayou-refinery.svg?color=blue)](https://pypi.org/project/sayou-refinery/) | **[Normalizer]** Converts complex structures into standard Markdown. |
| `sayou-chunking` | [![PyPI](https://img.shields.io/pypi/v/sayou-chunking.svg?color=blue)](https://pypi.org/project/sayou-chunking/) | **[Context-Aware Splitter]** Protects atomic blocks (tables/code). |
| `sayou-wrapper` | [![PyPI](https://img.shields.io/pypi/v/sayou-wrapper.svg?color=blue)](https://pypi.org/project/sayou-wrapper/) | **[Schema Enforcer]** Wraps data into `SayouNode` objects. |
| `sayou-assembler` | [![PyPI](https://img.shields.io/pypi/v/sayou-assembler.svg?color=blue)](https://pypi.org/project/sayou-assembler/) | **[Graph Builder]** Links nodes to create Parent-Child relationships. |
| `sayou-loader` | [![PyPI](https://img.shields.io/pypi/v/sayou-loader.svg?color=blue)](https://pypi.org/project/sayou-loader/) | **[Writer]** Saves graph to Files, BigQuery, or VectorDBs. |
| `sayou-extractor` | [![PyPI version](https://img.shields.io/pypi/v/sayou-extractor.svg?color=blue)](https://pypi.org/project/sayou-extractor/) | **[Query, Retrieve, Search]** Intelligent retrieval using Hybrid Search (Vector + Graph). |
| `sayou-llm` | [![PyPI version](https://img.shields.io/pypi/v/sayou-llm.svg?color=blue)](https://pypi.org/project/sayou-llm/) | **[OpenAI, Anthropic, Local]** An adapter layer for various LLMs. |
| `sayou-visualizer` | [![PyPI](https://img.shields.io/pypi/v/sayou-visualizer.svg?color=blue)](https://pypi.org/project/sayou-visualizer/) | **[Observability]** Live dashboard & 3D Knowledge Graph renderer. |

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
```bash
pip install sayou-visualizer
```

---

## 4. Quick Start

The `StandardPipeline` in `sayou-brain` acts as a Facade, abstracting away the complexity of the underlying modules. It intelligently routes data based on file types (PDF, Markdown, JSON, etc.).

### Step 1: Install

```python
from sayou.brain import StandardPipeline
```

### Step 2: Execute Process (ETL)

Just point to a file or a URL. The brain handles **Connecting -> Parsing -> Refining -> Chunking -> Wrapping -> Assembling -> Loading**.

```python
result = StandardPipeline().process(
    source="./reports/financial_q1.pdf",
    destination="knowledge_graph.json",
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
    { "……" }
  ],
  "edges": [
    { "……" }
  ]
}
```

---

## 5. Visualizer Showcase

Sayou Fabric creates beautiful, interactive visualizations of your data structure.

### 📊 Live DAG Tracing
Monitor the execution flow of your pipeline in real-time. See exactly which plugins are activated and how data flows between them.

<img src="https://github.com/sayouzone/sayou-fabric/blob/main/docs/assets/graph_tracer.png?raw=true" width="800">

### 🌌 3D Knowledge Graph (Holographic View)
Visualize your document structure as a 3D city. 
* **Red Cubes:** Documents (Virtual Parents)
* **Blue Orbs:** Chunks (Data Blocks)
* **Orange Octahedrons:** Headers (Structural Anchors)

<img src="https://github.com/sayouzone/sayou-fabric/blob/main/docs/assets/kg_renderer.png?raw=true" width="800">

---

## 6. Documentation & Contribution

* **[Official Documentation](https://sayouzone.github.io/sayou-fabric/)**
* **[Contributing Guide](CONTRIBUTING.md)**

We welcome contributions! Please feel free to submit Pull Requests for new Connectors, Parsers, or Loader plugins.

---

## 7. License

Apache 2.0 License © 2025 **Sayouzone**