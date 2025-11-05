# sayou-refinery

`sayou-refinery` provides a pipeline for **refining and processing** data `Atoms` (from `sayou-wrapper`). This includes cleaning, merging, and aggregating data.

---

## 1. Concepts (Core Interfaces)

This library is built on three T1 Interfaces, managed by the `RefineryPipeline`.

* **`BaseProcessor` (T1):** Defines a 1-to-1 transformation on a data `Atom` (e.g., cleaning a text field, imputing a missing value).
* **`BaseMerger` (T1):** Defines an N-to-N operation, joining multiple `Atoms` or lists of `Atoms` based on a common key.
* **`BaseAggregator` (T1):** Defines an N-to-1 operation, reducing a list of `Atoms` into a single summary `Atom` (e.g., calculating an average).

---

## 2. T2 Usage (Default Components)

`sayou-refinery` provides T2 components for common data cleaning tasks.

### Using `DefaultTextCleaner` (T2)
(Placeholder for text explaining this T2 component implements `BaseProcessor`. It is used to automatically strip HTML tags, remove extra whitespace, and normalize text within a specified `Atom` field.)

### Using `KeyBasedMerger` (T2)
(Placeholder for text explaining this T2 component implements `BaseMerger`. It joins two lists of `Atoms` based on a shared `entity_id` or other specified key, similar to a SQL JOIN.)

### Using `Deduplicator` (T2)
(Placeholder for text explaining this T2 component implements `BaseProcessor` and filters out `Atoms` that have a duplicate value in a specified field.)

---

## 3. T3 Plugin Development

A T3 plugin is used to add custom, complex business logic to your refinement pipeline.

### Tutorial: Building a `CustomOutlierRemover` (T3)
(Placeholder for a step-by-step text tutorial.)
1.  **Create your class:** Define `CustomOutlierRemover`.
2.  **Inherit T1:** Make your class inherit from `BaseProcessor` (T1).
3.  **Implement `_do_process`:** Inside this method, write your logic (e.g., using a statistical model) to check if an `Atom`'s value is an outlier. If it is, return `None` to filter it from the pipeline.
4.  **Use it:** Pass your `CustomOutlierRemover` instance to the `steps=[]` list in the `RefineryPipeline` constructor.

---

## 4. API Reference

### Tier 1: Interfaces

| Interface | File | Description |
| :--- | :--- | :--- |
| `BaseProcessor` | `interfaces/base_processor.py`| 1-to-1 transformation (e.g., clean, impute). |
| `BaseMerger` | `interfaces/base_merger.py` | N-to-N join operation. |
| `BaseAggregator`| `interfaces/base_aggregator.py`| N-to-1 summary operation. |

### Tier 2: Default Components

| Component | Directory | Implements |
| :--- | :--- | :--- |
| `DefaultTextCleaner`| `processor/` | `BaseProcessor` |
| `Deduplicator` | `processor/` | `BaseProcessor` |
| `Imputer` | `processor/` | `BaseProcessor` |
| `KeyBasedMerger` | `merger/` | `BaseMerger` |
| `AverageAggregator`| `aggregator/`| `BaseAggregator` |