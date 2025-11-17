# `sayou-refinery`

[![Build Status](https://img.shields.io/github/actions/workflow/status/sayouzone/sayou-fabric/ci.yml?branch=main)](https://github.com/sayouzone/sayou-fabric/actions)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://sayouzone.github.io/sayou-fabric/library-guides/refinery/)


`sayou-refinery` is the central data transformation and cleansing library for the Sayou Data Platform. It acts as the "smelter" in the data pipeline, taking raw extracted data and turning it into clean, usable content for downstream tasks like chunking, embedding, and RAG.

## Philosophy: Transformation, Not Extraction

`sayou-refinery` does not extract data from files; that is the job of `sayou-document` or `sayou-connector`.

Instead, `sayou-refinery`'s sole responsibility is **transformation**. It cleans, interprets, filters, and reformats data structures, making them intelligent and optimized for LLMs.

## 🚀 Key Features

`sayou-refinery` has a dual role:

1.  **Document Refining:** It "interprets" the rich, high-fidelity JSON output from `sayou-document` and transforms it into LLM-friendly formats like Markdown (`ContentBlock` objects).
2.  **DataAtom Refining:** It cleans and processes streams of `DataAtom` objects (from `sayou-connector` or `sayou-wrapper`) to reduce noise and enhance insights for RAG.

### Core Components

* **Doc Refiners (`doc/`):** Specialized tools for transforming `sayou-document` output.
    * `DocToMarkdownRefiner`: The (Tier 2) engine that converts a `document` JSON into a list of `ContentBlock` objects (Markdown, Images), interpreting `raw_attributes` to create semantic structure (like headings and lists).
* **Atom Processors (`processor/`):** (1:1) Cleans or transforms single `DataAtom`s.
    * e.g., `Deduplicator` (removes duplicates), `TextCleaner` (strips HTML).
* **Atom Aggregators (`aggregator/`):** (N:M) Summarizes or combines multiple `DataAtom`s into new ones.
    * e.g., `AverageAggregator` (calculates averages from time-series data).
* **Atom Mergers (`merger/`):** (N+E:N) Enriches `DataAtom`s with external data.
    * e.g., `KeyBasedMerger` (joins atoms with a CSV or database lookup).

## 📦 Installation

```bash
pip install sayou-refinery
```

## ⚡ Quickstart

`sayou-refinery` provides different tools for different data types.

### 1. Refining a Document (from `sayou-document`)

This example shows how `sayou-rag` uses `refinery` to process a document.

```python
import json
from sayou.refinery.processor.doc_to_markdown import DocToMarkdownRefiner

# 1. Load the JSON output from sayou-document
# (This assumes doc_data is a dict from doc.model_dump())
with open("my_document_output.json", "r", encoding="utf-8") as f:
    doc_data = json.load(f)

# 2. Initialize the Tier 2 refiner (default engine)
refiner = DocToMarkdownRefiner()
refiner.initialize()

# 3. Refine the dict into ContentBlocks (MD, image data, etc.)
content_blocks = refiner.refine(doc_data)

# 4. (Application Logic) Assemble and save the Markdown
final_markdown = []
for block in content_blocks:
    if block.type == "md":
        final_markdown.append(block.content)
    # (Add logic here to save images (block.type == "image_base64") and link them)

output = "\n\n".join(final_markdown)
# print(output)
```

### 2. Refining DataAtoms

This example shows how to clean a list of `DataAtom`s.

```python
from sayou.core.atom import DataAtom
from sayou.refinery.core.context import RefineryContext
from sayou.refinery.processor.deduplicator import Deduplicator

# 1. Prepare DataAtoms (e.g., from sayou-connector)
atoms = [
    DataAtom("source_A", "item", {"id": "123", "data": "A"}),
    DataAtom("source_B", "item", {"id": "456", "data": "B"}),
    DataAtom("source_C", "item", {"id": "123", "data": "C_dupe"})
]
context = RefineryContext(atoms=atoms)

# 2. Initialize the Tier 2 processor
# We want to deduplicate based on the 'id' field in the payload
deduper = Deduplicator()
deduper.initialize(key_field="payload.id")

# 3. Process the context
refined_context = deduper.process(context)

# refined_context.atoms will now only contain the first two atoms
# print(len(refined_context.atoms)) # Output: 2
```

## 🗺️ Roadmap

* Implementing more Tier 2 `Aggregator` templates (e.g., `SumAggregator`, `TimeSeriesResampler`).
* Developing Tier 3 plugins for advanced HTML-to-Markdown conversion.

## 🤝 Contributing

We welcome contributions! If you are interested in building new refiner plugins, please check our contributing guidelines (TODO) and open an issue.

## 📜 License

This project is licensed under the Apache 2.0 License.