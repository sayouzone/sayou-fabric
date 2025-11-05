# sayou-chunking

`sayou-chunking` provides a standardized, extensible framework for segmenting and splitting text documents.

---

## 1. Concepts (Core Interfaces)

This library is built around a single primary T1 Interface.

### BaseSplitter (T1)

The `BaseSplitter` is the core contract for all chunking logic. It defines the standard `split()` method that the `ChunkingPipeline` (or `sayou-rag`) uses to process text. Any T2 or T3 component that implements this interface can be hot-swapped into a pipeline.

---

## 2. T2 Usage (Default Splitters)

`sayou-chunking` provides several T2 (default) strategies in the `splitter/` directory, ready for immediate use.

### Using `RecursiveCharacterSplitter` (T2)
(Placeholder for text explaining this is the recommended default strategy for general-purpose text. It recursively tries to split text by a list of separators, such as newlines, spaces, etc.)

(Placeholder for a code-free explanation: "To use it, you initialize the `ChunkingPipeline` and pass an instance of `RecursiveCharacterSplitter` to its `splitters` list.")

### Using `SemanticSplitter` (T2)
(Placeholder for text explaining this advanced T2 strategy. It groups sentences based on embedding similarity, requiring an embedding model.)

---

## 3. T3 Plugin Development

A key feature of `sayou-fabric` is adding your own logic via T3 plugins. For example, you could wrap a third-party tool like LangChain.

### Tutorial: Building a `LangchainRecursiveSplitter` (T3)
(Placeholder for a step-by-step text tutorial.)
1.  **Create your class:** Define `LangchainRecursiveSplitter` in the `plugins/` folder.
2.  **Inherit T1:** Make your class inherit from `BaseSplitter` (T1).
3.  **Implement `_do_split`:** Inside the `_do_split` method (which T1 requires), you will call the `langchain.text_splitter` logic.
4.  **Use it:** You can now pass an instance of your `LangchainRecursiveSplitter` into the `ChunkingPipeline` just like a T2 component. The pipeline only sees the T1 interface and doesn't care if it's a T2 or T3.

---

## 4. API Reference

### Tier 1: Interfaces

| Interface | File | Description |
| :--- | :--- | :--- |
| `BaseSplitter` | `interfaces/base_splitter.py` | The single contract for all splitting components. |

### Tier 2: Default Components

| Component | Directory | Implements |
| :--- | :--- | :--- |
| `FixedLengthSplitter` | `splitter/` | `BaseSplitter` |
| `RecursiveSplitter` | `splitter/` | `BaseSplitter` |
| `SemanticSplitter` | `splitter/` | `BaseSplitter` |
| `StructureSplitter` | `splitter/` | `BaseSplitter` |
| ...etc | `splitter/` | `BaseSplitter` |

### Tier 3: Official Plugins

| Plugin | Directory | Implements/Wraps |
| :--- | :--- | :--- |
| `LangchainRecursiveSplitter`| `plugins/` | `BaseSplitter` |
| `AuditedFixedLengthSplitter`| `plugins/` | `FixedLengthSplitter` (T2) |