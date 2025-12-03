# Library Guide: sayou-refinery

`sayou-refinery` is the "smelter" of the Sayou Data Platform. Its single responsibility is **data transformation**. It takes raw data structures provided by extractors (`document`, `connector`) and transforms them into clean, structured, and intelligent formats for the next stage of the pipeline (`chunk`, `wrapper`, `rag`).

This library is crucial for **reducing noise and increasing signal** before feeding data to an LLM.

---

## 1. Independent Installation

To use `sayou-refinery` independently of the main `sayou-rag` package:

```bash
pip install sayou-refinery
```

---

## 2. Core Concepts: A Dual-Role Smelter

`sayou-refinery` is designed to handle two different types of data, and it provides a separate set of tools for each.



* **Path A: Document Refining**
    * **Input:** A single, large `Dict` (JSON) object from `sayou-document`.
    * **Action:** Interprets high-fidelity metadata (`raw_attributes`) to generate semantic content.
    * **Output:** A `List[SayouBlock]` (e.g., Markdown text, image data) ready for `sayou-chunk`.

* **Path B: DataAtom Refining**
    * **Input:** A `List[DataAtom]` (e.g., from `sayou-connector` or `sayou-wrapper`).
    * **Action:** Cleans, filters, summarizes, or enriches the `DataAtom`s.
    * **Output:** A new, refined `List[DataAtom]` ready for `sayou-assembler` or `sayou-rag`.

---

## 3. The `sayou-document` Contract (Input Specification)

The Document Refiner (`DocToMarkdownRefiner`) is a **specialist**, not a generalist. It is **explicitly designed to understand the output schema of `sayou-document`**.

It does *not* accept arbitrary JSON. It expects a `Dict` with the following structure:

```json
{
  "file_name": "str (e.g., 'report.docx')",
  "metadata": { "title": "str", "author": "str", "...": "..." },
  "pages": [
    {
      "page_num": "int",
      "elements": [
        {
          "type": "text",
          "text": "str (The actual text content)",
          "raw_attributes": {
            "semantic_type": "heading (or 'list', 'normal')",
            "heading_level": 1,
            "list_level": 0,
            "style": "str (e.g., 'Heading 1')"
          },
          "meta": { "page_num": "int", "id": "str" }
        },
        {
          "type": "image",
          "image_base64": "str (base64 encoded string)",
          "image_format": "str (e.g., 'png')",
          "ocr_text": "str (Text from OCR)",
          "meta": { "page_num": "int", "id": "str" }
        },
        {
          "type": "table",
          "data": [ ["Header 1"], ["Row 1 Cell 1"] ],
          "meta": { "page_num": "int", "id": "str" }
        },
        {
          "type": "chart",
          "text_representation": "str (LLM-friendly text of chart data)",
          "meta": { "page_num": "int", "id": "str" }
        }
      ],
      "footer_elements": [ "..." ]
    }
  ]
}
```

`sayou-refinery`'s job is to read these `raw_attributes` (like `semantic_type`) and make intelligent decisions (like converting to `# Heading`).

---

## 4. Key Components and Usage

### 4.1. Document Refiners (Tier 1: `BaseDocRefiner`)

This component transforms a `sayou-document` dictionary into `SayouBlock` objects.

* **Tier 2 (`doc/markdown.py`): `DocToMarkdownRefiner`**
    * This is the high-fidelity default engine. It reads the `raw_attributes` ("style", "semantic_type", "placeholder_type") to generate the richest possible Markdown, including headings (`#`), lists (`-`), tables, and image data.

```python
from sayou.refinery.processor.doc_to_markdown import DocToMarkdownRefiner
import json

# 1. Load the JSON dictionary from sayou-document
with open("my_document_output.json", "r", encoding="utf-8") as f:
    doc_data = json.load(f)

# 2. Initialize the Tier 2 refiner engine
# This engine knows how to read the spec above.
refiner = DocToMarkdownRefiner()
refiner.initialize(include_footers=False) # (Default: False)

# 3. Refine the dict into a list of SayouBlocks
# This list is the input for 'sayou-chunk'
content_blocks = refiner.refine(doc_data)

# content_blocks[0].type -> "md"
# content_blocks[0].content -> "--- (frontmatter) ---"
# content_blocks[1].type -> "md"
# content_blocks[1].content -> "# Heading Text"
# content_blocks[2].type -> "image_base64"
# content_blocks[2].content -> "iVBORw0KGgo..."
```

* **Output: `SayouBlock`**
    * The `refine()` method returns a `List[SayouBlock]`.
    * A `SayouBlock` is a simple dataclass with `type` (e.g., "md", "image_base64"), `content` (the data), and `metadata`.
    * `sayou-chunk` consumes this list directly.

### 4.2. DataAtom Refiners (Tier 1: `BaseProcessor`, `BaseAggregator`, `BaseMerger`)

These components operate on `List[DataAtom]` streams.

* **`BaseProcessor` (1:1 Transformation)**
    * *What it is:* A processor that transforms one atom at a time without reference to others.
    * *Tier 2 Examples:* `Deduplicator` (removes atoms with duplicate keys), `Imputer` (fills missing values), `TextCleaner` (strips HTML from a payload field).

```python
from sayou.core.atom import DataAtom
from sayou.refinery.core.context import RefineryContext
from sayou.refinery.processor.deduplicator import Deduplicator

atoms = [
    DataAtom("source", "item", {"id": "123", "data": "A"}),
    DataAtom("source", "item", {"id": "123", "data": "B_dupe"})
]
context = RefineryContext(atoms=atoms)

# Initialize processor with rules
deduper = Deduplicator()
deduper.initialize(key_field="payload.id")

# Process
refined_context = deduper.process(context)
# len(refined_context.atoms) == 1
```

* **`BaseAggregator` (N:M Transformation)**
    * *What it is:* A processor that consumes many atoms and produces one or more new *summary* atoms. This is critical for reducing noise for LLMs.
    * *Tier 2 Examples:* `AverageAggregator` (consumes 30 daily atoms, produces 1 "monthly average" atom).

```python
from sayou.core.atom import DataAtom
from sayou.refinery.core.context import RefineryContext
# T2 Template
from sayou.refinery.aggregator.average import AverageAggregator 
# T3 Plugin (Hypothetical)
from sayou.refinery.plugins.average import SubwayAverageRefiner 

# 1. Prepare 30 daily atoms (example)
atoms = [DataAtom("api", "ridership", {"...": "..."}), ...] # 30 atoms
context = RefineryContext(atoms=atoms)
            
# 2. Initialize Tier 3 Aggregator (which uses Tier 2 engine)
# This plugin knows *how* to find keys in 'ridership' atoms
aggregator = SubwayAverageRefiner()
aggregator.initialize()

# 3. Process
# This consumes 30 atoms and outputs 1 summary atom
refined_context = aggregator.process(context)
# len(refined_context.atoms) == 1
# refined_context.atoms[0].type == "refined_average"
```

* **`BaseMerger` (N+E:N Enrichment)**
    * *What it is:* A processor that enriches atoms by looking up information from an *external* data source (like a `dict` or database connection) provided in the `RefineryContext`.
    * *Tier 2 Examples:* `KeyBasedMerger` (takes an atom with `product_id: 123` and merges it with external data to add `product_name: "Widget"`).

---

## 5. Extending (Tier 3 Guide)

Tier 3 plugins are used to **override the default Tier 2 behavior**.

For example, the default `DocToMarkdownRefiner`(T2) converts `semantic_type: "heading"` to `# Heading`. A Tier 3 plugin (`plugins/semantic_html_refiner.py`) could inherit from it and override the `_handle_text` method to convert it to `<h1>Heading</h1>` instead.

```python
from sayou.refinery.processor.doc_to_markdown import DocToMarkdownRefiner
from sayou.refinery.interfaces.base_doc_refiner import SayouBlock
from typing import Dict, Any, List

class HtmlRefinerPlugin(DocToMarkdownRefiner):
    """
    (Tier 3) Overrides T2 behavior to output HTML instead of Markdown.
    """
    component_name = "HtmlRefinerPlugin"
    
    def _handle_text(self, element: Dict[str, Any], is_header: bool, is_footer: bool) -> List[SayouBlock]:
        """
        Overrides the _handle_text method.
        """
        text = element.get("text", "").strip()
        if not text:
            return []

        raw_attrs = element.get("raw_attributes", {})
        semantic_type = raw_attrs.get("semantic_type")
        
        content = ""
        if semantic_type == "heading":
            level = raw_attrs.get("heading_level", 1)
            content = f"<h{level}>{text}</h{level}>"
        elif semantic_type == "list":
            content = f"<li>{text}</li>"
        else:
            content = f"<p>{text}</p>"

        return [SayouBlock(
            type="html", 
            content=content, 
            metadata={
                "page_num": element.get("meta", {}).get("page_num"),
                "id": element.get("id"),
            }
        )]

# --- Usage ---
# refiner = HtmlRefinerPlugin()
# blocks = refiner.refine(doc_data)
# blocks[0].type == "html"
# blocks[0].content == "<h1>Heading Text</h1>"
```