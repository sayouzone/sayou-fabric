# Sayou Data Fabric

[한국어 (README.ko.md)](./README.ko.md)
> A Modular Open-Source Framework for Building LLM Data Pipelines

[![Build Status](https://img.shields.io/github/actions/workflow/status/sayouzone/sayou-fabric/ci.yml?branch=main)](https://github.com/sayouzone/sayou-fabric/actions)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://github.com/sayouzone/sayou-fabric/LICENSE)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://sayouzone.github.io/sayou-fabric/)

## 1. Core Architecture

`sayou-fabric` decomposes the LLM data pipeline by **data flow units** to provide the **stability**, **lightweight footprint**, and **extensibility** required for production environments.

### 1.1. Lightweight & Modular Packages

Every component in the `sayou-fabric` is deployed as an **independent Python package**.

* Users install only what they need: `pip install sayou-chunking`.
* Each library minimizes its dependencies (beyond `sayou-core`), preventing conflicts and ensuring lightweight container images.

### 1.2. Consistent 3-Tier Architecture (Interface → Default → Plugin)

All `sayou` libraries follow a consistent 3-Tier design:

* **Tier 1 – Interface:** The standard "socket" for the system (e.g., `BaseFetcher`, `BaseLLMClient`).
* **Tier 2 – Default:** The official, "batteries-included" implementation (e.g., `RecursiveCharacterSplitter`, `OpenAIClient`).
* **Tier 3 – Plugin:** The extension layer where users can plug in their own logic (e.g., an in-house DB connector, a custom LLM) by implementing a T1 interface.

### 1.3. Explicit & Composable Workflow

The `sayou-rag` `RAGExecutor` avoids implicit "magic." It explicitly runs the T1/T2/T3 nodes (Router, Tracer, Fetcher, Generator) that the user assembles. This ensures every step of the RAG pipeline is transparent, controllable, and debuggable.

## 2. Ecosystem Packages

`sayou-fabric` includes the following core libraries:

| Package | Status | Description |
| :--- | :--- | :--- |
| `sayou-core` | ![Beta](https://img.shields.io/badge/status-beta-brightgreen) | Core components (BaseComponent, Atom) |
| `sayou-connector` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] Data 'Ingestion' (API, File, DB...) |
| `sayou-wrapper` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] 'Wrap' data into a standard Atom |
| `sayou-chunking` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] Text 'Chunking' strategies |
| `sayou-refinery` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] Data 'Refinement' (Cleaner, Merger...) |
| `sayou-assembler` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] 'Assemble' data (KG Builder...) |
| `sayou-loader` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] 'Load' data (VectorDB, File...) |
| `sayou-extractor` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] 'Extract' data (Retriever, Querier...) |
| `sayou-llm` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] LLM 'Adapter' (OpenAI, Local LLM...) |
| `sayou-rag` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] RAG/Agent 'Workflow Executor' |

## 3. Installation

Install only the packages you need.

```bash
# Example 1: Install RAG pipeline with local LLM (Hugging Face)
pip install sayou-rag sayou-llm[transformers] sayou-extractor

# Example 2: Install data collection and chunking modules only
pip install sayou-connector sayou-chunking
```

Refer to the Official Docs for a full list of optional dependencies (extras).

## 4. Quick Start

## 5. Documentation

Full architecture guides, E2E tutorials, T3 plugin development guides, and API references are available at our **Official Docs Site**.

## 6. Contributing

Contributions are welcome via issues or pull requests. For major changes, please open an issue first to discuss what you would like to change.

**Git Branch Strategy**

- `main`: Production release branch (no direct commits).
- `develop`: Active development branch (all PRs should target this).
- `feature/`, `fix/`: Temporary branches created from develop.

**Workflow**
```Bash
# Sync latest develop branch
git checkout develop
git pull origin develop

# Create a new feature branch
git checkout -b feature/add-semantic-chunker

# Commit and push changes
git commit -m "feat(chunking): Add T2 SemanticChunker"
git push origin feature/add-semantic-chunker
```

## 7. License

sayou-fabric is distributed under the Apache License 2.0.