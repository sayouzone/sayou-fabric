# sayou-brain

[![Build Status](https://img.shields.io/github/actions/workflow/status/sayouzone/sayou-fabric/ci.yml?branch=main)](https://github.com/sayouzone/sayou-fabric/actions)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://sayouzone.github.io/sayou-fabric/sayou-agent/overview/)

`sayou-brain` is the **orchestrator** of the Sayou Data Platform. It integrates all individual libraries (`sayou-document`, `sayou-chunking`, `sayou-assembler`, etc.) into a single, coherent pipeline for Retrieval-Augmented Generation.

While other libraries focus on specific tasks (parsing, splitting, assembling), `sayou-brain` focuses on the **lifecycle of data**—from ingestion to inference. It serves as the primary entry point for developers building data-centric AI applications.

## Philosophy

**"One Interface, Two Worlds."**
Brain consists of two distinct phases: **Ingestion** (Write/ETL) and **Inference** (Read/QA).
`sayou-brain` provides a unified `StandardPipeline` that abstracts away the complexity of underlying modules, offering simple methods like `ingest()` and `ask()` to bridge these two worlds.

## 🚀 Key Features

* **Unified Control Tower:** Manages the entire flow from raw documents to LLM answers.
* **Smart Routing:** Automatically detects input types (File vs. Database) and routes data to the appropriate ETL path.
* **Dual-Mode Pipeline:**
    * **Ingestion Mode:** `File -> Document -> Refinery -> Chunking -> Wrapper -> Assembler -> Loader`
    * **Inference Mode:** `Query -> Extractor -> LLM`
* **Modular & Mockable:** Built on a 3-Tier architecture, allowing easy replacement of components (e.g., switching from local file storage to Neo4j/Pinecone).

## 📦 Installation

```python
pip install sayou-brain
```

## ⚡ Quickstart

You don't need to import individual libraries. The `StandardPipeline` handles everything internally.

### 1. Initialize the Pipeline

```python
from sayou.brain.pipeline.standard import StandardPipeline

# Initialize the orchestrator (loads all sub-pipelines)
brain = StandardPipeline()
brain.initialize()
```

### 2. Ingest Data (ETL)

Simply provide a file path. The pipeline creates a Knowledge Graph automatically.

```python
# This triggers: Document -> Refinery -> Chunking -> Wrapper -> Assembler -> Loader
target_file = "company_report.pdf"

result = brain.ingest(target_file, save_to="knowledge_graph.json")
print(f"Ingestion Status: {result['status']}")
```

### 3. Ask Questions (Inference)

Ask questions based on the ingested data.

```python
query = "What is the revenue growth this year?"

# This triggers: Extractor -> LLM
answer = brain.ask(query, load_from="knowledge_graph.json")
print(f"Answer: {answer}")
```

## 🗺️ Architecture

`sayou-brain` delegates tasks to specialized workers:

* **Parsing:** `sayou-document`
* **Cleaning:** `sayou-refinery`
* **Splitting:** `sayou-chunking`
* **Standardization:** `sayou-wrapper`
* **Construction:** `sayou-assembler`
* **Storage/Retrieval:** `sayou-loader` / `sayou-extractor` (Internal Mocks or Plugins)

## 🤝 Contributing

We welcome contributions! Please check the individual library repositories for specific logic improvements, or contribute here to improve the orchestration flow.

## 📜 License

Apache 2.0 License © 2025 Sayouzone