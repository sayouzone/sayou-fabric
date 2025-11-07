# Sayou Refinery

**A pluggable framework for refining raw Data Atoms into a coherent Knowledge Graph (KG) for advanced LLM applications.**

---

## 💡 Why Sayou Refinery?

`sayou_refinery` solves the core problem of organizing messy, disconnected data into a structured KG. This KG acts as a "map" for RAG pipelines, allowing LLMs to retrieve accurate, context-aware data, minimizing hallucinations and costs.

- **Pluggable Architecture:** Bring your own data store (Neo4j, JSON) or refinement logic.
- **Ontology-Driven:** Ensures all data conforms to your central schema.
- **Focused Responsibility:** Does one job well: **Refine & Link**. No connectors, no embedding logic.

---

## 🚀 Quick Start

```bash
pip install sayou-refinery
```

```Python
```

## 🏗️ Core Concepts

- Data Atom: The standard input unit. (Schema/structure explanation)
- Refiner (BaseRefiner): Cleans, aggregates, or transforms atoms. (e.g., averaging subway data)
- Linker (BaseLinker): Establishes relationships between nodes.
- Store (BaseStore): The output driver (JSON, Neo4j, etc.).

## 📜 License

Apache 2.0 License © 2025 Sayouzone