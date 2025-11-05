# sayou-extractor

`sayou-extractor` provides standardized interfaces for retrieving, querying, and searching for data from various sources like files, SQL databases, and vector stores.

---

## 1. Concepts (Core Interfaces)

This library provides three distinct T1 Interfaces (verbs) for data extraction, all managed by the `ExtractorPipeline`.

### `BaseRetriever` (T1)
This interface defines the contract for **Key-Value** or **File-based** lookups (e.g., "get this specific file"). It uses a `retrieve()` method.

### `BaseQuerier` (T1)
This interface defines the contract for **structured queries**, such as SQL or Cypher (e.g., "SELECT * FROM users WHERE..."). It uses a `query()` method.

### `BaseSearcher` (T1)
This interface defines the contract for **similarity search** (e.g., vector KNN). It uses a `search()` method.

---

## 2. T2 Usage (Default Components)

You use `sayou-extractor` by initializing the `ExtractorPipeline` and passing T2 components to the corresponding "verb" list.

### Using Retrievers (`FileRetriever`, T2)
(Placeholder for text explaining that `FileRetriever` is the default T2 for `retrieve()` calls. It reads from a local file system.)

(Placeholder for a code-free explanation: "You pass an instance of `FileRetriever` to the `retrievers=[]` argument of the `ExtractorPipeline`.)

### Using Queriers (`SqlQuerier`, T2)
(Placeholder for text explaining `SqlQuerier` is the T2 for `query()` calls. It uses SQLAlchemy to run standard SQL against a configured DB.)

(Placeholder for a code-free explanation: "You pass `SqlQuerier` to the `queriers=[]` argument. The pipeline will route any request with `type: 'sql'` to it.")

### Using Searchers (`VectorSearchTemplate`, T2)
(Placeholder for text explaining `VectorSearchTemplate` is an abstract T2, and that T3 plugins (like `PgvectorSearcher`) are the concrete implementations.)

---

## 3. T3 Plugin Development

A common use case is adding a T3 plugin to query a specific database, like Neo4j.

### Tutorial: Building a `Neo4jCypherQuerier` (T3)
(Placeholder for a step-by-step text tutorial.)
1.  **Create your class:** Define `Neo4jCypherQuerier` in the `plugins/neo4j/` folder.
2.  **Inherit T1:** Make your class inherit from `BaseQuerier` (T1).
3.  **Implement `_do_query`:** Inside this method, you will write the logic to connect to Neo4j and execute the Cypher query.
4.  **Use it:** You pass your new `Neo4jCypherQuerier` to the `queriers=[]` list in the `ExtractorPipeline`. The pipeline will now route requests with `type: 'cypher'` (which you define) to your T3 plugin.

---

## 4. API Reference

### Tier 1: Interfaces

| Interface | File | Description |
| :--- | :--- | :--- |
| `BaseRetriever` | `interfaces/base_retriever.py` | Contract for K-V/File retrieval. |
| `BaseQuerier` | `interfaces/base_querier.py` | Contract for structured (SQL) queries. |
| `BaseSearcher` | `interfaces/base_searcher.py`| Contract for similarity search. |

### Tier 2: Default Components

| Component | Directory | Implements |
| :--- | :--- | :--- |
| `FileRetriever` | `retriever/` | `BaseRetriever` |
| `SqlQuerier` | `querier/` | `BaseQuerier` |
| `VectorSearchTemplate`| `searcher/` | `BaseSearcher` |

### Tier 3: Official Plugins

| Plugin | Directory | Implements |
| :--- | :--- | :--- |
| `PgvectorSearcher`| `plugins/` | `VectorSearchTemplate` (T2) |
| `CypherQuerier` | `plugins/neo4j/` | `BaseQuerier` (T1) |