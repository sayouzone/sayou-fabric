# sayou-connector

[![PyPI version](https://img.shields.io/pypi/v/sayou-connector.svg?color=blue)](https://pypi.org/project/sayou-connector/)
[![License](https://img.shields.io/badge/License-Apache%202.0-red.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Docs](https://img.shields.io/badge/docs-mkdocs-success.svg?logo=materialformkdocs)](https://sayouzone.github.io/sayou-fabric/library-guides/connector/)

**The Universal Data Ingestion Engine**

`sayou-connector` provides a unified interface to fetch data from diverse sources—Local Files, Web URLs, and Databases—normalizing everything into a standard format called **SayouPacket**.

It separates the logic of **Navigation** (Generator) from **Retrieval** (Fetcher), enabling complex recursive crawling and pagination strategies out of the box.

## 📦 Installation

```bash
pip install sayou-connector
```

## ⚡ Quick Start

The `ConnectorPipeline` manages the feedback loop between Generators and Fetchers.

```python
from sayou.connector.pipeline import ConnectorPipeline

def run_demo():
    # 1. Initialize Pipeline
    pipeline = ConnectorPipeline()
    pipeline.initialize()

    # 2. Run (Example: Web Crawling)
    print("Starting Web Crawl...")
    
    # Returns an iterator of 'SayouPacket' objects
    packets = pipeline.run(
        source="https://news.daum.net/tech",
        strategy="web_crawl",
        link_pattern=r"https://v\.daum\.net/v/\d+",
        max_depth=1
    )

    # 3. Process Results (Stream)
    for packet in packets:
        if packet.success:
            print(f"[Fetched] {packet.task.uri}")
            # packet.data contains the extracted content (dict, bytes, etc.)
            print(f"   Data: {str(packet.data)[:50]}...")
        else:
            print(f"[Error] {packet.error}")

if __name__ == "__main__":
    run_demo()
```

## 🔑 Key Concepts

* **Strategies:** Switch execution modes effortlessly (`file`, `requests`, `sqlite`).
* **SayouPacket:** A standardized data container (Success/Fail status, Data, Metadata) ensuring type safety.
* **Feedback Loop:** Generators can dynamically create new tasks based on Fetcher results (e.g., finding new links, next DB page).

## 🤝 Contributing

We welcome contributions for new Fetchers (e.g., S3, Kafka) or Generators!

## 📜 License

Apache 2.0 License © 2025 Sayouzone