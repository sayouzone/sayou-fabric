# sayou-loader

`sayou-loader` is a low-level library focused on **translating** data into specific query languages (like SQL or Cypher) and **writing** that data to a destination. It is often used by `Assembler` or `Extractor` plugins.

---

## 1. Concepts (Core Interfaces)

* **`BaseTranslator` (T1):** The contract for **translating** a `sayou` standard object (like an `Atom` or `KnowledgeGraph`) into a language string (e.g., an `INSERT` statement or a `CREATE` node query).
* **`BaseWriter` (T1):** The contract for **executing** the translated string(s) against a target database or writing to a file.

---

## 2. T2 Usage (Default Components)

The T2 components in `sayou-loader` are designed to be used as tools by other libraries.

### Using `SqlTranslator` (T2)
(Placeholder for text explaining this T2 component can take an `Atom` and, based on a schema, generate a standard SQL `INSERT` or `UPDATE` statement.)

### Using `CypherTranslator` (T2)
(Placeholder for text explaining this T2 component can take a `KnowledgeGraph` object and generate a series of `CREATE` and `MERGE` Cypher statements.)

### Using `FileWriter` (T2)
(Placeholder for text explaining this T2 component implements `BaseWriter` and simply writes string data (like from `JsonTranslator`) to a local file.)

---

## 3. T3 Plugin Development

T3 plugins in this library are highly specific adapters for cloud or specialized databases.

### Tutorial: Building a `BigQueryWriter` (T3)
(Placeholder for a step-by-step text tutorial.)
1.  **Create your class:** Define `BigQueryWriter` in the `plugins/` folder.
2.  **Inherit T1:** Make your class inherit from `BaseWriter` (T1).
3.  **Implement `_do_write`:** This method receives data (e.g., from `SqlTranslator`).
4.  **Add Logic:** Inside the method, use the `google-cloud-bigquery` client to connect and execute the load job.
5.  **Use it:** Your `BigQueryWriter` can now be used by any component (like `Assembler`) that needs to write to BigQuery.

---

## 4. API Reference

### Tier 1: Interfaces

| Interface | File | Description |
| :--- | :--- | :--- |
| `BaseTranslator`| `interfaces/base_translator.py`| Contract for translating objects to query strings. |
| `BaseWriter` | `interfaces/base_writer.py` | Contract for writing/executing data. |

### Tier 2: Default Components

| Component | Directory | Implements |
| :--- | :--- | :--- |
| `SqlTranslator` | `translator/` | `BaseTranslator` |
| `CypherTranslator`| `translator/` | `BaseTranslator` |
| `JsonTranslator` | `translator/` | `BaseTranslator` |
| `FileWriter` | `writer/` | `BaseWriter` |

### Tier 3: Official Plugins

| Plugin | Directory | Implements/Wraps |
| :--- | :--- | :--- |
| `BigQueryWriter` | `plugins/` | `BaseWriter` (T1) |
| `Neo4jWriter` | `plugins/` | `BaseWriter` (T1) |