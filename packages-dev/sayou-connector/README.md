# Sayou Connector

**A modular ingestion layer for bringing data into the Sayou Data Platform from APIs, files, or databases.**

---

## 💡 Why Sayou Connector?

`sayou_connector` abstracts how data gets into your pipelines.  
It standardizes fetchers and seeders so that other modules (Refinery, Assembler, etc.) can work on a consistent format.

- **Pluggable Sources:** API, S3, Salesforce, or your custom fetcher.  
- **Composable Pipelines:** Mix fetchers, generators, and seeders seamlessly.  
- **Schema-Aware Output:** Emits standardized `DataAtom` objects.

---

## 🚀 Quick Start

```bash
pip install sayou-connector
```

```python
```

## 🏗️ Core Concepts

- Fetcher – Retrieves data from external sources.
- Generator – Creates new atoms programmatically.
- Seeder – Feeds data into the system for testing or initialization.

## 📜 License

Apache 2.0 License © 2025 Sayouzone