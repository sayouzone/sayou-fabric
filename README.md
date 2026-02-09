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

## 1. Philosophy

**Sayou Fabric is a framework for Deterministic Knowledge Graph Construction.**

We focus on transforming unstructured data into structured assets by analyzing their intrinsic topology—syntax trees, file hierarchies, and metadata. This approach ensures that the constructed Knowledge Graph is precise, reproducible, and structurally sound, strictly following the data's native organization.

### 1.1. Structure-First Architecture

We prioritize the native structure of data to build a solid skeleton before processing the content.
* **Code**: Parsed via AST to deterministically link Classes, Methods, and Import dependencies.
* **Media**: Structured via Temporal Timeline and Semantic Segmentation.
* **Docs**: Hierarchically organized by Headers, Tables, and Layout Coordinates.

### 1.2. The 3-Tier Design Pattern

Inspired by robust enterprise architectures, every component adheres to a strict hierarchy to ensure stability at scale:
* **Tier 1 (Interface)**: The immutable contract defining behavior.
* **Tier 2 (Template)**: Standardized logic for ETL pipelines (Battery-included).
* **Tier 3 (Plugin)**: Vendor-specific implementations (e.g., YouTube, GitHub, Notion).

```mermaid
graph TD
    %% 스타일 정의
    classDef brain fill:#673ab7,stroke:#4527a0,color:white,stroke-width:2px;
    classDef modules fill:#e3f2fd,stroke:#1565c0,stroke-width:1px;
    classDef core fill:#455a64,stroke:#263238,color:white,stroke-width:2px;

    %% 노드 정의
    Brain[Sayou Brain
    < Orchestrator >]:::brain
    
    subgraph Libs [Functional Libraries]
        direction LR
        Conn[Connector]
        Doc[Document]
        Ref[Refinery]
        Chunk[Chunking]
        Wrap[Wrapper]
        Assem[Assembler]
    end
    
    Core[Sayou Core
    < Ontology & Schema >]:::core

    %% 연결
    Brain --> Libs
    Libs --> Core
    
    %% 정렬 힌트 (Libs 내부)
    Conn ~~~ Doc ~~~ Ref ~~~ Chunk ~~~ Wrap ~~~ Assem

    %% 스타일 적용
    class Conn,Doc,Ref,Chunk,Wrap,Assem modules
```

---

## 2. The Ecosystem

Sayou Fabric consists of independent, loosely coupled libraries that work together seamlessly.

| Package | Version | Description |
| :--- | :--- | :--- |
| `sayou-core` | [![PyPI](https://img.shields.io/pypi/v/sayou-core.svg?color=blue)](https://pypi.org/project/sayou-core/) | Foundational layer defining Schemas, Ontology, and base components. |
| `sayou-brain` | [![PyPI](https://img.shields.io/pypi/v/sayou-brain.svg?color=blue)](https://pypi.org/project/sayou-brain/) | Manages the entire lifecycle of data processing pipelines. |
| `sayou-connector` | [![PyPI](https://img.shields.io/pypi/v/sayou-connector.svg?color=blue)](https://pypi.org/project/sayou-connector/) | Universal ingestor with auto-source detection and streaming support. |
| `sayou-document` | [![PyPI](https://img.shields.io/pypi/v/sayou-document.svg?color=blue)](https://pypi.org/project/sayou-document/) | Parses documents while preserving layout, styles, and spatial coordinates. |
| `sayou-refinery` | [![PyPI](https://img.shields.io/pypi/v/sayou-refinery.svg?color=blue)](https://pypi.org/project/sayou-refinery/) | Normalizes data formats and removes noise or PII. |
| `sayou-chunking` | [![PyPI](https://img.shields.io/pypi/v/sayou-chunking.svg?color=blue)](https://pypi.org/project/sayou-chunking/) | Splits text intelligently based on context (Code, Markdown, Time). |
| `sayou-wrapper` | [![PyPI](https://img.shields.io/pypi/v/sayou-wrapper.svg?color=blue)](https://pypi.org/project/sayou-wrapper/) | Maps raw data to the Sayou Ontology and creates standardized Nodes. |
| `sayou-assembler` | [![PyPI](https://img.shields.io/pypi/v/sayou-assembler.svg?color=blue)](https://pypi.org/project/sayou-assembler/) | Constructs semantic relationships (Edges) between Nodes. |
| `sayou-loader` | [![PyPI](https://img.shields.io/pypi/v/sayou-loader.svg?color=blue)](https://pypi.org/project/sayou-loader/) | Exports the constructed Knowledge Graph to Databases or Files. |
| `sayou-extractor` | [![PyPI version](https://img.shields.io/pypi/v/sayou-extractor.svg?color=blue)](https://pypi.org/project/sayou-extractor/) | Retrieves context using Hybrid Search (Vector + Graph). |
| `sayou-llm` | [![PyPI version](https://img.shields.io/pypi/v/sayou-llm.svg?color=blue)](https://pypi.org/project/sayou-llm/) | A unified adapter interface for various LLM providers. |
| `sayou-visualizer` | [![PyPI](https://img.shields.io/pypi/v/sayou-visualizer.svg?color=blue)](https://pypi.org/project/sayou-visualizer/) | Visualizes the pipeline flow and renders 3D Knowledge Graphs. |

---

## 3. Installation

You can install the entire suite via the orchestrator package:

```bash
pip install sayou-brain
```

Or install individual components as needed for a lightweight setup:

```bash
pip install sayou-chunking sayou-document
```
```bash
pip install sayou-visualizer
```

---

## 4. Quick Start

The `sayou-brain` package provides high-level facades that abstract away the complexity of underlying modules. Choose the pipeline that fits your data source.

### Case A: Document Processing (PDF, Office)

Use `StandardPipeline` for layout-preserving document analysis.

```mermaid
flowchart LR
    %% 노드 스타일
    classDef input fill:#fff3e0,stroke:#e65100;
    classDef process fill:#f3e5f5,stroke:#7b1fa2;
    classDef output fill:#e8f5e9,stroke:#2e7d32;

    Input[PDF / Office]:::input
    
    subgraph SP [Standard Pipeline]
        direction LR
        C(Connector) --> D(Document Layout Parse)
        D --> R(Refinery)
        R --> CH(Chunking)
        CH --> W(Wrapper)
        W --> A(Assembler)
    end
    
    KG[("Knowledge Graph")]:::output

    Input --> C
    A --> L(Loader)
    L --> KG

    %% 강조
    style D stroke-width:3px,stroke:#d32f2f
```

```python
from sayou.brain import StandardPipeline

result = StandardPipeline().process(
    source="./reports/financial_q1.pdf",
    destination="knowledge_graph.json",
)

print(f"Ingestion Complete. Processed: {result['processed']}")
```

### Case B: Multimedia & Code Analysis

Use `NormalPipeline` for logic-based extraction from Video, Code repositories, or Web sources.

```mermaid
flowchart LR
    %% 노드 스타일
    classDef input fill:#fff3e0,stroke:#e65100;
    classDef process fill:#e1f5fe,stroke:#0277bd;
    classDef output fill:#e8f5e9,stroke:#2e7d32;

    Input[YouTube / Code]:::input
    
    subgraph NP [Normal Pipeline]
        direction LR
        C(Connector) --> R(Refinery)
        R --> CH(Chunking)
        CH --> W(Wrapper)
        W --> A(Assembler)
    end
    
    KG[("Knowledge Graph")]:::output

    Input --> C
    A --> L(Loader)
    L --> KG
    
    %% 강조
    style CH stroke-width:3px,stroke:#0288d1
```

```python
from sayou.brain import NormalPipeline

result = NormalPipeline().process(
    source="youtube://YOUTUBE_VIDEO_ID",
    destination="./output/graph_data.json"
)

print(f"Graph Construction Complete. Nodes: {len(result['nodes'])}")
```

### Output Format (JSON)

The output is a structured JSON strictly following the `Sayou Ontology`, ready for Graph Databases or Vector Stores.

<details> <summary><b>Click to expand JSON example</b></summary>

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

</details>

---

## 5. Visualizer Showcase

Observability is crucial for data engineering. Sayou Fabric provides built-in rendering tools to inspect your data topology and pipeline flow.

### 📊 Pipeline Telemetry (DAG Tracer)
Monitor the execution flow. Visualize which plugins are activated and verify how data transforms across the pipeline.

<img src="https://github.com/sayouzone/sayou-fabric/blob/main/docs/assets/graph_tracer.png?raw=true" width="800">

### 🌌 Holographic Knowledge Graph
Transform raw data into an interactive KG city.

* **Analytics Knowledge View**: Inspect strict node properties and relationships for debugging.

<img src="https://github.com/sayouzone/sayou-fabric/blob/main/docs/assets/kg_analytic.png?raw=true" width="800">

* **Showcase Knowledge View**: Visualize the cluster and semantic density of your knowledge base.

<img src="https://github.com/sayouzone/sayou-fabric/blob/main/docs/assets/kg_showcase.png?raw=true" width="800">

---

## 6. Documentation & Contribution

Sayou Fabric is currently in **Public Beta (v0.4.0)**. We are actively stabilizing the core engine and expanding the adapter ecosystem to support more enterprise data sources.

* **[Official Documentation](https://sayouzone.github.io/sayou-fabric/)**
* **[Contributing Guide](CONTRIBUTING.md)**

---

## 7. License

Apache 2.0 License © 2026 **Sayouzone**