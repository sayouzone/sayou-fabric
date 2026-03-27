# ── Setup
"""
Parse a PDF file into a structured `Document` using `DocumentPipeline`.

`PdfParser` uses PyMuPDF (fitz) to extract text blocks and images from
each page.  It also detects scanned pages automatically: if a page
contains no extractable text, it renders the page to a raster image and
passes it to the configured OCR engine (if any).

Install the dependency before running with a real file:

```bash
pip install pymupdf
python quick_start_pdf.py
```

The example below uses `DocumentPipeline.process()` — a one-line facade
that creates an instance, parses the file, and returns the `Document`.
"""
import json
from unittest.mock import MagicMock, patch

from sayou.document.models import Document, ImageElement, Page, TextElement
from sayou.document.pipeline import DocumentPipeline

OUTPUT_FILE = "pdf_result.json"


# ── Parse a Text PDF
"""
Pass raw bytes and the original filename.  `DocumentPipeline` selects
the best parser automatically via `can_handle()` scoring.

`doc.pages` is a list of `Page` objects, one per PDF page.
Each page exposes:
- `page.elements`  — list of `TextElement` / `ImageElement` objects
- `page.text`      — raw text dump of the page (for quick access)
- `page.page_num`  — 1-based page number
"""


def _make_fitz_page(text="Introduction to Sayou Fabric."):
    page = MagicMock()
    page.rect.width = 612.0
    page.rect.height = 792.0
    page.get_text.side_effect = lambda *a, **k: (
        {
            "blocks": [
                {
                    "type": 0,
                    "number": 0,
                    "bbox": (72, 72, 540, 90),
                    "lines": [{"spans": [{"text": text}]}],
                }
            ]
        }
        if a and a[0] == "dict"
        else text
    )
    return page


def _make_fitz_doc(pages):
    doc = MagicMock()
    doc.page_count = len(pages)
    doc.load_page.side_effect = lambda i: pages[i]
    doc.get_toc.return_value = [[1, "Introduction", 1], [2, "Architecture", 3]]
    return doc


with patch("sayou.document.parser.pdf_parser.fitz") as mock_fitz:
    mock_fitz.TEXTFLAGS_DICT = 0
    mock_fitz.open.return_value = _make_fitz_doc(
        [
            _make_fitz_page(
                "Sayou Fabric is a collection of LLM data-processing libraries."
            ),
            _make_fitz_page("The Brain orchestrator coordinates all eight packages."),
        ]
    )

    doc = DocumentPipeline.process(
        file_bytes=b"%PDF-1.4 fake",
        file_name="sayou_overview.pdf",
    )

print("=== Parse a Text PDF ===")
print(f"  doc_type   : {doc.doc_type}")
print(f"  page_count : {doc.page_count}")
print(f"  toc entries: {len(doc.toc)}")
for page in doc.pages:
    elems = [e for e in page.elements if isinstance(e, TextElement)]
    print(
        f"  Page {page.page_num}: {len(elems)} text element(s) — {elems[0].text[:50]!r}"
    )


# ── Access Structured Elements
"""
`TextElement` carries the extracted text in `.text` plus optional styling
in `.style` (font name, size, bold/italic flags).

`ImageElement` stores the raw image as `.image_base64` and, when an OCR
engine is attached, the extracted text as `.ocr_text`.

`BoundingBox` (`.bbox`) records the element's position in points:
`x0`, `y0` (top-left) and `x1`, `y1` (bottom-right).
"""
with patch("sayou.document.parser.pdf_parser.fitz") as mock_fitz:
    mock_fitz.TEXTFLAGS_DICT = 0
    img_block = {
        "type": 1,
        "number": 1,
        "bbox": (200, 300, 400, 500),
        "image": b"\x89PNG\r\n\x1a\n" + b"\x00" * 8,
        "ext": "png",
    }
    page = MagicMock()
    page.rect.width = 612.0
    page.rect.height = 792.0
    page.get_text.side_effect = lambda *a, **k: (
        {
            "blocks": [
                {
                    "type": 0,
                    "number": 0,
                    "bbox": (72, 72, 540, 90),
                    "lines": [{"spans": [{"text": "Figure 1: Architecture Diagram"}]}],
                },
                img_block,
            ]
        }
        if a and a[0] == "dict"
        else "Figure 1: Architecture Diagram"
    )
    fitz_doc = MagicMock()
    fitz_doc.page_count = 1
    fitz_doc.load_page.return_value = page
    fitz_doc.get_toc.return_value = []
    mock_fitz.open.return_value = fitz_doc

    doc2 = DocumentPipeline.process(b"%PDF-fake", "mixed.pdf")

page = doc2.pages[0]
text_elems = [e for e in page.elements if isinstance(e, TextElement)]
image_elems = [e for e in page.elements if isinstance(e, ImageElement)]

print("\n=== Access Structured Elements ===")
for e in text_elems:
    print(f"  TextElement  bbox=({e.bbox.x0:.0f},{e.bbox.y0:.0f}) text={e.text!r}")
for e in image_elems:
    b64_len = len(e.image_base64) if e.image_base64 else 0
    print(f"  ImageElement bbox=({e.bbox.x0:.0f},{e.bbox.y0:.0f}) base64_len={b64_len}")


# ── Table of Contents
"""
`doc.toc` is a list of dicts extracted from the PDF bookmark tree.
Each entry contains `level`, `title`, and `page_num`.
"""
print("\n=== Table of Contents ===")
with patch("sayou.document.parser.pdf_parser.fitz") as mock_fitz:
    mock_fitz.TEXTFLAGS_DICT = 0
    pg = _make_fitz_page("Content")
    fdoc = _make_fitz_doc([pg])
    fdoc.get_toc.return_value = [
        [1, "Introduction", 1],
        [1, "Architecture", 3],
        [2, "Connector", 4],
        [2, "Chunking", 6],
        [1, "Getting Started", 8],
    ]
    mock_fitz.open.return_value = fdoc
    doc3 = DocumentPipeline.process(b"%PDF-fake", "guide.pdf")

for entry in doc3.toc:
    indent = "  " * (entry["level"] - 1)
    print(f"  {indent}[L{entry['level']}] {entry['title']}  (p.{entry['page_num']})")


# ── Save Results
"""
`Document` is a Pydantic model — serialize with `.model_dump()`.
"""
output = doc.model_dump()
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nSaved Document to '{OUTPUT_FILE}'")
