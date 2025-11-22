# Sayou RAG: The Data Platform Orchestrator

Welcome to **Sayou RAG**.
This is the command center of the Sayou Data Platform.

If individual libraries like `sayou-document` or `sayou-chunking` are the **engine parts** (pistons, gears, valves), then `sayou-rag` is the **Car**. It assembles these parts into a working vehicle that takes you from "Raw Data" to "Intelligent Answers."

---

## 1. The Two Pillars of RAG

We architected `sayou-rag` around two fundamental lifecycles of data.

### Phase 1: Ingestion Pipeline (The Builder)
* **Goal:** Turn unstructured chaos into structured knowledge.
* **Process:** This is a heavy, batch-oriented process.
    1.  **Connect:** Fetch data from files or APIs.
    2.  **Parse:** Extract high-fidelity data (`sayou-document`).
    3.  **Refine:** Convert to standard Markdown (`sayou-refinery`).
    4.  **Chunk:** Split based on structure and context (`sayou-chunking`).
    5.  **Wrap:** Enforce company schema (`sayou-wrapper`).
    6.  **Assemble:** Build the Knowledge Graph (`sayou-assembler`).
    7.  **Load:** Persist to Vector DB or Graph DB (`sayou-loader`).

### Phase 2: Inference Pipeline (The Solver)
* **Goal:** Retrieve precise context and generate answers.
* **Process:** This is a real-time, latency-sensitive process.
    1.  **Extract:** Search KG/Vector Store for relevant nodes (`sayou-extractor`).
    2.  **Generate:** Synthesize answers using LLMs (`sayou-llm`).

---

## 2. Smart Routing & Automation

The core innovation of `sayou-rag` is the **`StandardPipeline`**. It acts as an intelligent router that decides how to process input data without user intervention.

**Scenario A: "I have a PDF file."**

```python
rag.ingest("manual.pdf")
```

* **Logic:** Detects file path -> Activates `DocumentPipeline` -> Full ETL Process.

**Scenario B: "I have raw text or JSON."**

```python
rag.ingest({"text": "..."})
```

* **Logic:** Detects Dict input -> Skips Parsing -> Activates `WrapperPipeline` directly.

---

## 3. Dependency Map

`sayou-rag` sits at the top of the hierarchy. It does not contain complex parsing or splitting logic itself; it imports and orchestrates them.
* **Upstream:** `sayou-connector`
* **Midstream (Processing):** `sayou-document`, `sayou-refinery`, `sayou-chunking`
* **Midstream (Structure):** `sayou-wrapper`, `sayou-assembler`
* **Downstream:** `sayou-loader`, `sayou-extractor`, `sayou-llm`

---

## 4. Getting Started

For detailed usage of the pipeline, refer to the **Quickstart** guide in the README or explore the specific guides for each component library in the left sidebar.

To begin building your own RAG application, simply install the main package:

```python
pip install sayou-rag
```

And initialize the standard pipeline:

```python
from sayou.rag.pipeline.standard import StandardPipeline
rag = StandardPipeline()
rag.initialize()
```