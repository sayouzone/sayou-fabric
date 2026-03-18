---
title: Library Guides
hide:
  - toc
---

# Library Guides

Sayou Fabric is composed of independent Python packages. Each follows the same [3-Tier design pattern](../get-started/architecture.md) — install only what you need, replace any component at any layer.

```bash
pip install sayou-brain        # full stack
pip install sayou-chunking     # just the splitter
```

---

| Package | Version | Description |
| :--- | :---: | :--- |
| [`sayou-brain`](brain.md) | [![PyPI](https://img.shields.io/pypi/v/sayou-brain.svg?color=4f8ef7)](https://pypi.org/project/sayou-brain/) | Pipeline orchestrator — wires all modules together |
| [`sayou-connector`](connector.md) | [![PyPI](https://img.shields.io/pypi/v/sayou-connector.svg?color=4f8ef7)](https://pypi.org/project/sayou-connector/) | Universal ingestor — files, APIs, databases, SaaS |
| [`sayou-document`](document.md) | [![PyPI](https://img.shields.io/pypi/v/sayou-document.svg?color=4f8ef7)](https://pypi.org/project/sayou-document/) | Layout-preserving parser — PDF, Office, Image |
| [`sayou-refinery`](refinery.md) | [![PyPI](https://img.shields.io/pypi/v/sayou-refinery.svg?color=4f8ef7)](https://pypi.org/project/sayou-refinery/) | Data cleaning, normalization, PII masking |
| [`sayou-chunking`](chunking.md) | [![PyPI](https://img.shields.io/pypi/v/sayou-chunking.svg?color=4f8ef7)](https://pypi.org/project/sayou-chunking/) | Polyglot structural splitter with AST call-graph |
| [`sayou-wrapper`](wrapper.md) | [![PyPI](https://img.shields.io/pypi/v/sayou-wrapper.svg?color=4f8ef7)](https://pypi.org/project/sayou-wrapper/) | Chunk → typed `SayouNode` with ontology mapping |
| [`sayou-assembler`](assembler.md) | [![PyPI](https://img.shields.io/pypi/v/sayou-assembler.svg?color=4f8ef7)](https://pypi.org/project/sayou-assembler/) | Node → Edge resolution — CALLS, INHERITS, IMPORTS… |
| [`sayou-loader`](loader.md) | [![PyPI](https://img.shields.io/pypi/v/sayou-loader.svg?color=4f8ef7)](https://pypi.org/project/sayou-loader/) | Persistence — VectorDB, Graph DB, JSON |
| [`sayou-extractor`](extractor.md) | [![PyPI](https://img.shields.io/pypi/v/sayou-extractor.svg?color=4f8ef7)](https://pypi.org/project/sayou-extractor/) | Hybrid search — Vector + Graph retrieval |
| [`sayou-llm`](llm.md) | [![PyPI](https://img.shields.io/pypi/v/sayou-llm.svg?color=4f8ef7)](https://pypi.org/project/sayou-llm/) | Unified LLM adapter interface |
| [`sayou-visualizer`](visualizer.md) | [![PyPI](https://img.shields.io/pypi/v/sayou-visualizer.svg?color=4f8ef7)](https://pypi.org/project/sayou-visualizer/) | 3D KG rendering and pipeline DAG tracing |