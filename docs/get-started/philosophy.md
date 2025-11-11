# Philosophy

Sayouzone's Data Platform is built on three core principles that define its value and design.

### 1. The Facade Principle: "Low Floor, High Ceiling"
Our goal is to provide the simplest possible entry point for a complex task.

* **Low Floor (Easy Start):** The `BasicRAG` facade. You import *one* class (`BasicRAG`) and provide *one* function (`map_logic`). The framework handles the rest. This gets you from "API-to-Answer" in minutes.

* **High Ceiling (High Customization):** When you outgrow the facade, you have full access to the underlying libraries (Lego bricks). Want to swap the `FileStorer` for a `Neo4jStorer`? Import `AssemblerPipeline` and configure it yourself. You are never locked into the "basic" flow.

### 2. Built for Production and Scale
Sayou is engineered for production-grade systems. We believe that a scalable RAG system *is* a scalable data engineering system.

This "Process-Driven" philosophy is why Sayou is not a single library. It is a composable set of 11+ specialized modules (Connector, Wrapper, Assembler...). Each module is built with a 3-Tier (Interface -> Default -> Plugin) architecture, ensuring that every single component of your pipeline can be tested, customized, and replaced as your application scales.

### 3. The Knowledge Graph as a Reusable Asset
A Sayou pipeline doesn't just produce an answer in memory. **It produces a tangible, structured, and reusable data asset: the Knowledge Graph** (`final_kg.json`).

This KG is not a "black box" like a vector database index. It's a clean, auditable JSON file that can be:

* **Queried** again later without re-running the API.

* **Imported** into a graph database like Neo4j.

* **Used** for analytics or visualization.

* **Versioned** and managed as part of your data infrastructure.