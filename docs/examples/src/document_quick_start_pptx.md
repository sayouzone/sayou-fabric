!!! abstract "Source"
    Synced from [`packages/sayou-document/examples/quick_start_pptx.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-document/examples/quick_start_pptx.py).

## Setup

Parse a PowerPoint (.pptx) presentation into a structured `Document` using
`DocumentPipeline`.

`PptxParser` iterates through every slide and extracts shapes by type:
text frames, pictures, tables, and charts.  Group shapes are recursively
expanded.  Speaker notes are captured in `slide.note_text`.

Install the dependency before running with a real file:

```bash
pip install python-pptx
python quick_start_pptx.py
```

```python
import json
from unittest.mock import MagicMock, patch

from sayou.document.models import (ChartElement, Document, ImageElement, Slide,
                                   TableElement, TextElement)
from sayou.document.pipeline import DocumentPipeline

OUTPUT_FILE = "pptx_result.json"
```

## Parse Slides

Each slide becomes a `Slide` object in `doc.pages`.

`Slide` carries:
- `.elements`   — shapes extracted from the slide body
- `.text`       — concatenated text of all shapes (for quick access)
- `.note_text`  — speaker notes (empty string if none)
- `.has_notes`  — `True` when speaker notes are present
- `.page_num`   — 1-based slide index

```python
def _text_shape(text, shape_id, top=0):
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    s = MagicMock()
    s.shape_id = shape_id
    s.has_text_frame = True
    s.text = text
    s.left = 100
    s.top = top
    s.width = 400
    s.height = 50
    s.shape_type = MSO_SHAPE_TYPE.TEXT_BOX
    s.is_placeholder = False
    return s


def _picture_shape(shape_id):
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    s = MagicMock()
    s.shape_id = shape_id
    s.has_text_frame = False
    s.text = ""
    s.left = 400
    s.top = 100
    s.width = 200
    s.height = 150
    s.shape_type = MSO_SHAPE_TYPE.PICTURE
    s.is_placeholder = False
    s.image.blob = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
    s.image.ext = "png"
    return s


def _table_shape(rows, shape_id):
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    s = MagicMock()
    s.shape_id = shape_id
    s.has_text_frame = False
    s.text = ""
    s.left = 100
    s.top = 200
    s.width = 500
    s.height = 200
    s.shape_type = MSO_SHAPE_TYPE.TABLE
    s.is_placeholder = False
    mock_rows = []
    for row_data in rows:
        row = MagicMock()
        row.cells = [MagicMock(text=c) for c in row_data]
        mock_rows.append(row)
    s.table.rows = mock_rows
    return s


def _make_slide(shapes, note=""):
    slide = MagicMock()
    slide.shapes = shapes
    slide.has_notes_slide = bool(note)
    if note:
        slide.notes_slide.notes_text_frame.text = note
    return slide


with patch("sayou.document.parser.pptx_parser.Presentation") as MockPrs:
    MockPrs.return_value.slides = [
        _make_slide(
            shapes=[
                _text_shape("Sayou Fabric", 1, top=50),
                _text_shape("LLM Data Pipeline Library", 2, top=120),
                _picture_shape(3),
            ],
            note="Welcome everyone. Start with the overview.",
        ),
        _make_slide(
            shapes=[
                _text_shape("Architecture", 1, top=50),
                _table_shape(
                    [
                        ["Layer", "Library", "Output"],
                        ["Collect", "Connector", "SayouPacket"],
                        ["Parse", "Document", "Document"],
                        ["Normalise", "Refinery", "SayouBlock"],
                        ["Chunk", "Chunking", "SayouChunk"],
                    ],
                    shape_id=2,
                ),
            ],
        ),
        _make_slide(
            shapes=[
                _text_shape("Getting Started", 1, top=50),
                _text_shape("pip install sayou-core sayou-chunking", 2, top=120),
            ],
            note="Live demo after this slide.",
        ),
    ]

    doc = DocumentPipeline.process(b"PK\x03\x04", "sayou_deck.pptx")

print("=== Parse Slides ===")
print(f"  doc_type   : {doc.doc_type}")
print(f"  slide_count: {doc.page_count}")
for slide in doc.pages:
    assert isinstance(slide, Slide)
    notes_tag = f" [NOTE: {slide.note_text[:30]!r}]" if slide.has_notes else ""
    print(f"  Slide {slide.page_num}: {len(slide.elements)} element(s){notes_tag}")
    for e in slide.elements:
        tag = type(e).__name__.replace("Element", "")
        preview = (
            e.text[:40]
            if hasattr(e, "text") and isinstance(e.text, str)
            else (
                f"base64={len(e.image_base64)} chars"
                if isinstance(e, ImageElement)
                else ""
            )
        )
        print(f"    [{tag:6s}] {preview!r}")
```

## Speaker Notes

Iterate slides and collect notes for all slides that have them.

```python
print("\n=== Speaker Notes ===")
for slide in doc.pages:
    if slide.has_notes:
        print(f"  Slide {slide.page_num}: {slide.note_text!r}")
```

## Element Type Distribution

Count element types per slide — useful for understanding deck density.

```python
print("\n=== Element Type Distribution ===")
for slide in doc.pages:
    counts = {}
    for e in slide.elements:
        t = type(e).__name__
        counts[t] = counts.get(t, 0) + 1
    print(f"  Slide {slide.page_num}: {counts}")
```

## Save Results

```python
output = doc.model_dump()
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nSaved Document to '{OUTPUT_FILE}'")
```