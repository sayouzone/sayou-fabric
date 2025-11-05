# Installation

This section explains how to install Sayou Data Fabric and its modular components.

---

## 1. Prerequisites

- Python 3.9 or higher
- pip ≥ 23.0
- (Optional) virtual environment recommended

```bash
python -m venv venv
source venv/bin/activate   # or .\venv\Scripts\activate on Windows
```

## 2. Installation Options

Install only what you need.

```bash
# Example 1: RAG pipeline with local LLM support
pip install sayou-rag "sayou-llm[transformers]" sayou-extractor

# Example 2: Data collection and chunking only
pip install sayou-connector sayou-chunking
```

## 3. Verify Installation

```bash
python -m sayou.core --version
```

## 4. Next Steps

- Read the **[Architecture](architecture.md)** section to understand the internal structure.
- Explore the **[Library Guides](../library-guides/core.md)** for module-level details.