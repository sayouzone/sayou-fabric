# sayou-rag

`sayou-rag` is the **Orchestration Engine** of the Sayou Fabric. It does not provide a single pipeline, but rather an **`RAGExecutor`** that runs a "graph" of composable "nodes" (components) to execute complex RAG and Agentic workflows.

---

## 1. Concepts (Core Interfaces)

`sayou-rag` defines the T1 interfaces for each "node" in a RAG workflow.

* **`BaseRouter` (T1):** The contract for classifying a user's query (e.g., "Is this a billing question or a general question?").
* **`BaseTracer` (T1):** The contract for tracing a "route" to a specific data source (e.g., "Billing questions map to the `billing_db`").
* **`BaseTransformer` (T1):** The contract for transforming the user's query (e.g., HyDE, Sub-query generation).
* **`BaseFetcher` (T1):** The contract for retrieving context from a source (e.g., `sayou-extractor`).
* **`BaseGenerator` (T1):** The contract for generating a final response using the context (e.g., `sayou-llm`).

---

## 2. T2 Usage (Assembling a Pipeline)

You do not "use" `sayou-rag`. You **"assemble"** it. The T2 components (in `router/`, `fetcher/`, etc.) are "nodes" that you give to the `RAGExecutor`.

### Example: Assembling an Agentic RAG
(Placeholder for a text-based explanation of the E2E example.)
1.  **Instantiate Tools:** Create instances of your tools (e.g., `sayou-extractor` and `sayou-llm`).
2.  **Instantiate T2 Nodes:**
    * `SayouSftRouter` (T2) is given the `sayou-llm` client for routing.
    * `KgTracer` (T2) is given the `sayou-extractor` for KG lookups.
    * `VectorFetcher` (T2) is given the `sayou-extractor` for vector search.
    * `LlmGenerator` (T2) is given the `sayou-llm` client for generation.
3.  **Instantiate Executor:** Pass all four T2 nodes to the `RAGExecutor`.
4.  **Run:** Call `executor.run(query)`. The executor will automatically run the nodes in the correct order (Router -> Tracer -> Fetcher -> Generator).

### Example: Assembling a Simple RAG
(Placeholder for text explaining that if you only pass a `Fetcher` and a `Generator` to the `RAGExecutor`, it will automatically skip the (Router/Tracer) steps and run a simpler pipeline.)

---

## 3. T3 Plugin Development

A T3 plugin in `sayou-rag` is a custom "node" in the graph, such as a Reranker.

### Tutorial: Building a `CohereReranker` (T3)
(Placeholder for a step-by-step text tutorial.)
1.  **Create your class:** Define `CohereRerankerPlugin`.
2.  **Inherit T1?** No, a Reranker is a special step. It might **wrap** a `BaseFetcher` (T1).
3.  **Wrap `fetch`:** Create a T3 class `RerankingFetcher(BaseFetcher)`.
4.  **Add Logic:** Its `__init__` takes a T2 `VectorFetcher` and a Cohere client. Its `_do_fetch` method first calls the T2 `VectorFetcher` to get 50 documents, then passes them to Cohere's Rerank API, and finally returns only the top 5.
5.  **Use it:** Pass your `RerankingFetcher` (T3) to the `fetcher=` argument of the `RAGExecutor`.

---

## 4. API Reference

### Tier 1: Interfaces

| Interface | File | Description |
| :--- | :--- | :--- |
| `BaseRouter` | `interfaces/base_router.py` | Contract for query classification. |
| `BaseTracer` | `interfaces/base_tracer.py` | Contract for mapping routes to sources. |
| `BaseTransformer`| `interfaces/base_transformer.py`| Contract for query transformation. |
| `BaseFetcher` | `interfaces/base_fetcher.py` | Contract for context retrieval. |
| `BaseGenerator`| `interfaces/base_generator.py`| Contract for final response generation. |

### Tier 2: Default Components

| Component | Directory | Implements |
| :--- | :--- | :--- |
| `SftRouter` | `router/` | `BaseRouter` |
| `KgTracer` | `tracer/` | `BaseTracer` |
| `HydeTransformer`| `transformer/` | `BaseTransformer` |
| `VectorFetcher` | `fetcher/` | `BaseFetcher` |
| `LlmGenerator` | `generator/` | `BaseGenerator` |

### Tier 3: Official Plugins

| Plugin | Directory | Implements/Wraps |
| :--- | :--- | :--- |
| `CohereReranker` | `plugins/` | Wraps `BaseFetcher` (T1) |