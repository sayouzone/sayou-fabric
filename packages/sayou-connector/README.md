# sayou-connector

[![Build Status](https://img.shields.io/github/actions/workflow/status/sayouzone/sayou-fabric/ci.yml?branch=main)](https://github.com/sayouzone/sayou-fabric/actions)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://sayouzone.github.io/sayou-fabric/library-guides/connector/)

`sayou-connector` is the **universal data ingestion engine** for the Sayou Data Platform. It provides a unified interface to fetch data from diverse sources—Local Files, Web URLs, APIs, and Databases.

Unlike simple HTTP clients or file readers, `sayou-connector` is designed as a **Recursive Crawling Engine**. It separates the logic of "What to fetch" (Navigation) from "How to fetch" (Transport), allowing for complex, stateful data collection strategies like web crawling or database pagination.

## Philosophy

**"Navigate First, Fetch Later."**
Data collection is not a one-off task; it's a discovery process.
We define two distinct roles:
1.  **Generator (Navigator):** Determines the next target (e.g., finds the next page URL, calculates DB offset).
2.  **Fetcher (Driver):** Executes the retrieval (e.g., sends HTTP GET, executes SQL).

This separation allows the pipeline to be infinitely extensible—from a simple file walker to an AI-powered web crawler.

## 🚀 Key Features

* **Strategy-Based Execution:** Switch between `local_scan`, `web_crawl`, or `sql_scan` with a single parameter.
* **Recursive & Stateful:** Supports BFS/DFS crawling for websites and directories with depth control.
* **Smart Filtering:** Built-in support for regex-based URL filtering and file extension filtering.
* **AI-Ready:** Designed to integrate with LLMs (Tier 3 Plugin) to intelligently identify CSS selectors or generate SQL queries dynamically.

## 📦 Installation

```python
pip install sayou-connector
```

## ⚡ Quickstart

The `ConnectorPipeline` manages the loop between Generators and Fetchers.

```python
from sayou.connector.pipeline import ConnectorPipeline

def run_demo():
    # 1. Initialize Pipeline
    pipeline = ConnectorPipeline()
    pipeline.initialize()

    # 2. Run (Example: Web Crawling)
    print("Starting Web Crawl...")
    results = pipeline.run(
        source="BASE_URL",
        strategy="web_crawl",
        # Generator Options
        link_pattern="BASE_PATTERN",
        max_depth=1
    )

    # 3. Process Results (Stream)
    for res in results:
        print(f"[Fetched] {res.task.uri}")
        # res.data contains extracted content or raw HTML
        # res.task contains metadata

if __name__ == "__main__":
    run_demo()
```

## 🤝 Contributing

We welcome contributions for new Fetchers (e.g., S3Fetcher, KafkaFetcher) or Generators (e.g., SitemapGenerator).

## 📜 License

Apache 2.0 License © 2025 Sayouzone