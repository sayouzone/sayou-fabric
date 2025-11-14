# `sayou-document`

[![Build Status](https://img.shields.io/github/actions/workflow/status/sayouzone/sayou-fabric/ci.yml?branch=main)](https://github.com/sayouzone/sayou-fabric/actions)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://sayouzone.github.io/sayou-fabric/library-guides/document/)

`sayou-document` is a high-fidelity document parsing library for Python. It converts various document formats (PDF, DOCX, PPTX, XLSX) into a **single, unified JSON structure**, focusing on extracting rich, structured data, not just plain text.

This library is the foundational "Extractor" component of the **Sayou Data Platform**, designed for data-driven AI and advanced RAG pipelines that require more than just text.

## Philosophy

We believe LLMs are powerful but not infallible. **Logic should be handled by engineers, not probability.**

`sayou-document` is **not** an "interpreter." It does not guess if a bold text is a "title." It is an **"extractor."** It captures the raw facts—"this text is bold, 16pt, and at (x0, y0)"—preserving the original document's fidelity. This rich, structured data is then passed to `sayou-refinery` for intelligent, rule-based processing.

## 🚀 Key Features

* **Unified Schema:** One consistent JSON structure for all document types.
* **High-Fidelity:** Extracts text, tables, images, charts, bounding boxes, and metadata.
* **Multi-Format:** Out-of-the-box support for:
    * PDF (`.pdf`)
    * Word (`.docx`)
    * PowerPoint (`.pptx`)
    * Excel (`.xlsx`)
* **Layout Preservation:** Captures headers, footers (Word), table of contents (PDF), and slide notes (PPTX).
* **Pluggable OCR:** Easily integrate any OCR engine (like Google Vision) to extract text from scanned PDFs and embedded images.
* **Part of an Ecosystem:** Designed to be the first step, feeding structured data into `sayou-refinery`, `sayou-chunking`, and ultimately `sayou-rag`.

## 📦 Installation

```bash
pip install sayou-document

# To include default OCR capabilities or converters (optional)
# pip install sayou-document[ocr]
```

## ⚡ Quickstart

The `DocumentPipeline` is the only object you need. It automatically routes the file to the correct parser and returns a standardized `Document` object.

```python
import os
from sayou.document.pipeline import DocumentPipeline
# Optional: Add an OCR engine plugin
# from sayou.document.plugins.ocr import GoogleVisionOCR

# 1. Initialize the pipeline
pipeline = DocumentPipeline()

# Optional: Inject an OCR engine (Tier 3 Plugin)
# ocr_engine = GoogleVisionOCR(credentials="path/to/creds.json")
# pipeline = DocumentPipeline(ocr_engine=ocr_engine)

pipeline.initialize()

# 2. Load your file
file_path = "path/to/your/document.pptx"
file_name = os.path.basename(file_path)

with open(file_path, "rb") as f:
    file_bytes = f.read()

# 3. Run the pipeline
try:
    # 'doc' is a Pydantic object
    doc = pipeline.run(file_bytes, file_name)

    # 4. Get the unified JSON output
    json_output = doc.model_dump_json(indent=2)

    # Save the result
    with open(f"parsed_{file_name}.json", "w", encoding="utf-8") as f:
        f.write(json_output)
    
    print(f"Successfully parsed {file_name}")

except ValueError as e:
    print(f"Error parsing {file_name}: {e}")
```

### Example JSON Output (Truncated)

The `Document` object provides a clean, predictable structure.

```json
{
  "file_name": "document.pptx",
  "file_id": "document.pptx",
  "doc_type": "slide",
  "metadata": {
    "title": "My Presentation",
    "author": "Sayou"
  },
  "page_count": 1,
  "pages": [
    {
      "page_num": 1,
      "width": 1280.0,
      "height": 720.0,
      "elements": [
        {
          "id": "p1:shape:100",
          "type": "text",
          "bbox": { "x0": 100.0, "y0": 50.0, "x1": 500.0, "y1": 100.0 },
          "raw_attributes": {
            "placeholder_type": "TITLE"
          },
          "text": "This is the Main Title",
          "meta": { "page_num": 1, "id": "p1:shape:100" }
        },
        {
          "id": "p1:shape:101",
          "type": "chart",
          "bbox": { "x0": 100.0, "y0": 150.0, "x1": 600.0, "y1": 400.0 },
          "raw_attributes": {
            "series_count": 2
          },
          "chart_title": "Sales Data",
          "chart_type": "BAR_CLUSTERED",
          "text_representation": "Chart: Sales Data...\n- Series 1: [10, 20, 30]\n",
          "meta": { "page_num": 1, "id": "p1:shape:101" }
        }
      ],
      "note_text": "Remember to emphasize the Q4 growth."
    }
  ],
  "toc": []
}
```

## 🗺️ Roadmap (v0.1.0+)

`sayou-document` v0.0.1 provides a robust foundation. Our next steps focus on deepening the "High-Fidelity" promise:

* **Annotations:** Extracting PDF comments, highlights, and sticky notes.
* **Advanced Styles:** Capturing detailed cell-level formatting (borders, fills) from Excel and Word tables.
* **Structural Semantics:** Parsing footnotes, endnotes, and list structures (bullets/numbering) from Word.
* **HWP Support:** Adding a (Tier 3) converter plugin for `.hwp` files.

## 🤝 Contributing

We welcome contributions! If you are interested in improving `sayou-document` or building new parsers/plugins, please check our contributing guidelines (TODO) and open an issue.

## 📜 License

This project is licensed under the Apache 2.0 License.