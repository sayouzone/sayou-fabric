# sayou-document

(Note: This library is planned for a future release. This document outlines the intended architecture.)

`sayou-document` provides advanced capabilities for parsing, understanding, and extracting structured data from complex unstructured documents (e.g., PDFs, DOCX, images).

---

## 1. Concepts (Core Interfaces)

This library will introduce T1 interfaces for a high-level document processing pipeline.

* **`BaseParser` (T1):**
    (Placeholder text: Defines the contract for converting a raw file (like a PDF or DOCX) into a clean, text-based intermediate representation.)

* **`BaseLayoutAnalyzer` (T1):**
    (Placeholder text: Defines the contract for analyzing the *structure* of a parsed document, identifying elements like tables, headers, paragraphs, and figures.)

* **`BaseExtractor` (T1):**
    (Placeholder text: Defines the contract for extracting specific entities (e.g., invoice numbers, customer names) using the analyzed layout and text.)

---

## 2. T2 Usage (Default Components)

(Placeholder text: T2 components for this library are under active development. Default implementations, such as a `PyMuPDFParser` (for `BaseParser`) or a `TableTransformerAnalyzer` (for `BaseLayoutAnalyzer`), will be provided for common document processing tasks.)

---

## 3. T3 Plugin Development

A T3 plugin for `sayou-document` would allow you to integrate specialized, third-party document AI services.

### Tutorial: Building a `GoogleDocumentAIExtractor` (T3)

(Placeholder for a step-by-step text tutorial.)
1.  **Create your class:** Define `GoogleDocumentAIExtractor`.
2.  **Inherit T1:** Make your class inherit from `BaseExtractor` (T1).
3.  **Implement `_do_extract`:** Inside this method, write the logic to call the Google Document AI API with the parsed document data.
4.  **Return Data:** Format the JSON response from Google's API to match the `sayou` standard output.
5.  **Use it:** Pass your `GoogleDocumentAIExtractor` instance to your `RAGExecutor`'s fetcher/parser nodes to use it instead of the T2 default.

---

## 4. API Reference

### Tier 1: Interfaces

| Interface | File | Description |
| :--- | :--- | :--- |
| `BaseParser` | `interfaces/base_parser.py` | (Planned) Contract for parsing raw document files. |
| `BaseLayoutAnalyzer`| `interfaces/base_analyzer.py`| (Planned) Contract for analyzing document structure. |
| `BaseExtractor` | `interfaces/base_extractor.py` | (Planned) Contract for extracting entities from documents. |

### Tier 2: Default Components

| Component | Directory | Implements |
| :--- | :--- | :--- |
| (TBD) | `parser/` | `BaseParser` |
| (TBD) | `analyzer/` | `BaseLayoutAnalyzer` |

### Tier 3: Official Plugins

(Placeholder text: No official plugins are available for this module yet.)