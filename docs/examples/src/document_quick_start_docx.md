!!! abstract "Source"
    Synced from [`packages/sayou-document/examples/quick_start_docx.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-document/examples/quick_start_docx.py).

## Setup

Parse a Microsoft Word (.docx) file into a structured `Document` using
`DocumentPipeline`.

`DocxParser` uses `python-docx` to traverse the document body, extracting
paragraphs (with heading / list semantic types), tables, and inline images
from body, headers, and footers.

Install the dependency before running with a real file:

```bash
pip install python-docx
python quick_start_docx.py
```

The example uses a mock so it runs without any `.docx` file on disk.

```python
import io
import json
from unittest.mock import MagicMock, patch

from sayou.document.models import Document, Page, TableElement, TextElement
from sayou.document.pipeline import DocumentPipeline
```

## Parse Paragraphs and Tables

`DocxParser` maps paragraph styles to semantic types stored in
`element.raw_attributes`:

| Style                  | `semantic_type` | extra key         |
|------------------------|-----------------|-------------------|
| `Heading 1` – `9`      | `"heading"`     | `heading_level`   |
| `List Bullet / Number` | `"list"`        | `list_level`      |
| Normal / other         | (none)          | —                 |

Tables become `TableElement` objects with:
- `.data`  — 2-D list of strings (LLM-friendly)
- `.cells` — list of `TableCell` with `is_header`, `row_span`, `col_span`

```python
def _make_para(text, style_name="Normal", style_id="Normal"):
    para = MagicMock()
    para.text = text
    para.style.name = style_name
    para.style.style_id = style_id
    from docx.enum.style import WD_STYLE_TYPE

    para.style.type = WD_STYLE_TYPE.PARAGRAPH
    para._p = MagicMock()
    para._p.pPr = None
    run = MagicMock()
    run.text = text
    run._element.xml = "<w:r/>"
    para.runs = [run]
    return para


def _make_table(rows):
    tbl = MagicMock()
    mock_rows = []
    for row_data in rows:
        row = MagicMock()
        row.cells = [MagicMock(text=c) for c in row_data]
        mock_rows.append(row)
    tbl.rows = mock_rows
    return tbl


with patch("sayou.document.parser.docx_parser.DocxDocument") as MockDoc, patch(
    "sayou.document.parser.docx_parser.Paragraph"
) as MockPara, patch("sayou.document.parser.docx_parser.Table") as MockTable:

    mock_doc = MagicMock()
    mock_doc.sections = []

    paras = [
        _make_para("Sayou Fabric Overview", "Heading 1", "Heading1"),
        _make_para("Introduction", "Heading 2", "Heading2"),
        _make_para("Architecture", "Heading 2", "Heading2"),
        _make_para("First bullet", "List Bullet", "ListBullet"),
        _make_para("Second bullet", "List Bullet", "ListBullet"),
        _make_para("Plain paragraph describing the system."),
    ]
    tables = [
        _make_table(
            [
                ["Library", "Purpose", "Output"],
                ["Connector", "Data collection", "SayouPacket"],
                ["Document", "File parsing", "Document"],
                ["Refinery", "Content normalization", "SayouBlock"],
                ["Chunking", "Text splitting", "SayouChunk"],
            ]
        )
    ]

    class _FakeBody:
        def __iter__(self_inner):
            for p in list(paras):
                m = MagicMock()
                m.tag = "p"
                m.tag.endswith = lambda s: s == "p"
                yield m
            for t in list(tables):
                m = MagicMock()
                m.tag = "tbl"
                m.tag.endswith = lambda s: s == "tbl"
                yield m

    mock_doc.element.body = _FakeBody()
    MockDoc.return_value = mock_doc
    para_q = list(paras)
    table_q = list(tables)
    MockPara.side_effect = lambda e, d: para_q.pop(0) if para_q else MagicMock()
    MockTable.side_effect = lambda e, d: table_q.pop(0) if table_q else MagicMock()

    doc = DocumentPipeline.process(b"PK\x03\x04", "overview.docx")

page = doc.pages[0]
text_elems = [e for e in page.elements if isinstance(e, TextElement)]
table_elems = [e for e in page.elements if isinstance(e, TableElement)]

print("=== Parse Paragraphs and Tables ===")
print(f"  doc_type     : {doc.doc_type}")
print(f"  text elements: {len(text_elems)}")
print(f"  table elements:{len(table_elems)}")
for e in text_elems:
    stype = e.raw_attributes.get("semantic_type", "text")
    level = e.raw_attributes.get("heading_level", "")
    tag = f"{stype}({level})" if level else stype
    print(f"    [{tag:12s}] {e.text!r}")
```

## Inspect Table Structure

The first row's cells have `is_header=True` (heuristic: first row = header).
Each `TableCell` also has `row_span` and `col_span` (currently 1; merge
detection is planned for v0.1.0).

```python
if table_elems:
    tbl = table_elems[0]
    print("\n=== Inspect Table Structure ===")
    print(f"  Rows: {len(tbl.data)}  Cols: {len(tbl.data[0])}")
    print(f"  Header row: {tbl.data[0]}")
    for row_cells in tbl.cells[:3]:
        for cell in row_cells:
            mark = " [H]" if cell.is_header else ""
            print(f"    {cell.text:25s}{mark}")
        print()
```

## Save Results

`Document.model_dump()` serialises the full element tree to a plain dict.

```python
output = doc.model_dump()
with open("docx_result.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("Saved Document to 'docx_result.json'")
```