# sayou-assembler

`sayou-assembler` **builds** complex, in-memory data structures (like Knowledge Graphs or Vector Indexes) from refined `Atoms` and **stores** them in a final destination.

---

## 1. Concepts (Core Interfaces)

This library is built on two T1 Interfaces, managed by the `AssemblerPipeline`.

* **`BaseBuilder` (T1):** The contract for **assembling** a list of `Atoms` into a final, structured object *in memory* (e.g., a `KnowledgeGraph` object).
* **`BaseStorer` (T1):** The contract for **persisting** that in-memory object to a destination (e.g., a file, a database).

This library also uses `SchemaManager` and `SchemaValidator` (from its `utils/` directory) to validate `Atoms` against a formal ontology before building.

---

## 2. T2 Usage (Default Components)

### Using `DefaultKGBuilder` (T2)
(Placeholder for text explaining this T2 builder iterates over `Atoms`, identifies `entity_id`s, `attributes`, and `relationships`, and builds a standard `KnowledgeGraph` object in memory.)

### Using `DefaultVectorBuilder` (T2)
(Placeholder for text explaining this T2 builder extracts text content and metadata from `Atoms` and prepares them for a vector store format.)

### Using `FileStorer` (T2)
(Placeholder for text explaining this T2 storer takes the output from a `Builder` (like a `KnowledgeGraph` object) and serializes it to a JSON file on disk.)

---

## 3. T3 Plugin Development

A T3 plugin is used to store the assembled object in a specialized database.

### Tutorial: Building a `Neo4jStorer` (T3)
(Placeholder for a step-by-step text tutorial.)
1.  **Create your class:** Define `Neo4jStorer` in the `plugins/` folder.
2.  **Inherit T1:** Make your class inherit from `BaseStorer` (T1).
3.  **Implement `_do_store`:** This method receives the `KnowledgeGraph` object from the T2 `DefaultKGBuilder`.
4.  **Add Logic:** Inside the method, write logic to connect to Neo4j (using `neo4j-driver`) and translate the graph object's nodes and edges into Cypher queries, then execute them.
5.  **Use it:** Pass your `Neo4jStorer` instance to the `storer=` argument of the `AssemblerPipeline` constructor.

---

## 4. API Reference

### Tier 1: Interfaces

| Interface | File | Description |
| :--- | :--- | :--- |
| `BaseBuilder` | `interfaces/base_builder.py` | Contract for assembling `Atoms` in memory. |
| `BaseStorer` | `interfaces/base_storer.py` | Contract for persisting the built object. |

### Tier 2: Default Components

| Component | Directory | Implements |
| :--- | :--- | :--- |
| `DefaultKGBuilder` | `builder/` | `BaseBuilder` |
| `DefaultVectorBuilder`| `builder/` | `BaseBuilder` |
| `FileStorer` | `storer/` | `BaseStorer` |

### Tier 3: Official Plugins

| Plugin | Directory | Implements/Wraps |
| :--- | :--- | :--- |
| `Neo4jStorer` | `plugins/` | `BaseStorer` (T1) |