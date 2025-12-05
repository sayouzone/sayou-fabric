# sayou-brain

[![PyPI version](https://img.shields.io/pypi/v/sayou-brain.svg?color=blue)](https://pypi.org/project/sayou-brain/)
[![License](https://img.shields.io/badge/License-Apache%202.0-red.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Docs](https://img.shields.io/badge/docs-mkdocs-success.svg?logo=materialformkdocs)](https://sayouzone.github.io/sayou-fabric/sayou-agent/overview/)

**The Central Nervous System of Sayou Fabric.**

`sayou-brain` is the all-in-one orchestrator that connects and manages the entire lifecycle of data within the Sayou ecosystem. Instead of manually wiring `connector` → `document` → `refinery` → ... → `loader`, you simply ask the Brain to **"Ingest this"**, and it handles the rest.

It serves as the **Control Plane**, managing configurations, routing data based on types, and executing the ETL pipeline efficiently.

## 💡 Core Philosophy

**"Simplicity for Users, Power for Developers."**

* **For Users:** A single entry point (`StandardPipeline`) to build complex RAG pipelines without boilerplate code.
* **For Developers:** A modular architecture where every stage (Parse, Chunk, Embed) is swappable via strategies and plugins.

```mermaid
flowchart LR
    User -->|Ingest(source, dest)| Brain[StandardPipeline]
    Brain --> Connector
    Brain --> Document
    Brain --> Refinery
    Brain --> Chunking
    Brain --> Wrapper
    Brain --> Assembler
    Brain --> Loader
    Loader -->|Save| DB[(Database)]
```

## 📦 Installation

Installing `sayou-brain` automatically installs all core dependencies and sub-modules.

```bash
pip install sayou-brain
```

## ⚡ Quick Start

#### 1. Basic Usage (Zero Config)

The simplest way to ingest a local folder into a Knowledge Graph file.

```python
from sayou.brain.pipelines.standard import StandardPipeline

def run_simple():
    # 1. Initialize
    brain = StandardPipeline()
    brain.initialize()

    # 2. Ingest Data (End-to-End)
    # Reads local files -> Parses -> Chunks -> Assembles Graph -> Saves JSON
    result = brain.ingest(
        source="./my_documents",
        destination="./output_graph.json"
    )
    
    print(f"Processed: {result['processed']} files.")

if __name__ == "__main__":
    run_simple()
```

#### 2. Advanced Usage (With Configuration & Strategies)

Customize behavior using `config` and specific `strategies`.

```python
import yaml
from sayou.brain.pipelines.standard import StandardPipeline

def run_advanced():
    # 1. Load Configuration (e.g., for PII masking, Chunk size)
    config_yaml = """
    refinery:
      mask_email: true
    chunking:
      chunk_size: 500
    """
    config = yaml.safe_load(config_yaml)

    # 2. Initialize Brain with Config
    brain = StandardPipeline()
    brain.initialize(config=config)

    # 3. Ingest with specific strategies
    result = brain.ingest(
        source="https://news.daum.net/tech",
        destination="./news_graph.json",
        strategies={
            "connector": "web_crawl",    # Crawl the web
            "chunking": "markdown",      # Respect markdown structure
            "assembler": "graph",        # Build a knowledge graph
            "loader": "file"             # Save to local file
        }
    )
    print(f"Result: {result}")
```

## 🔑 Key Components

- `StandardPipeline`: The default ETL flow. It intelligently routes data based on file types.
    - Images → Auto-converted to PDF → OCR
    - Markdown/Text → Bypasses Parser → Direct to Refinery
    - JSON/DB Rows → Treated as structured Records
- `Config`: Centralized configuration management. Parameters passed to `brain.initialize()` are propagated down to every sub-module.

## 🤝 Contributing

We welcome contributions for new pipeline flows (e.g., `RealtimePipeline` for streaming data, `RagPipeline` for inference).

## 📜 License

Apache 2.0 License © 2025 Sayouzone