!!! abstract "Source"
    Synced from [`packages/sayou-document/examples/quick_start_excel.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-document/examples/quick_start_excel.py).

## Setup

Parse a Microsoft Excel (.xlsx) workbook into a structured `Document` using
`DocumentPipeline`.

`ExcelParser` treats each worksheet as a `Sheet` (subclass of `BasePage`).
Cell data is wrapped in a `TableElement`; embedded images become
`ImageElement` objects.  A built-in repair mechanism handles workbooks with
corrupted metadata XML (common with third-party export tools).

Install the dependency before running with a real file:

```bash
pip install openpyxl
python quick_start_excel.py
```

```python
import json
from unittest.mock import MagicMock, patch

from sayou.document.models import Document, Sheet, TableElement
from sayou.document.pipeline import DocumentPipeline

OUTPUT_FILE = "excel_result.json"
```

## Parse a Workbook

Each `Sheet` in `doc.pages` corresponds to one worksheet.

`Sheet` fields:
- `.sheet_name`  — worksheet title
- `.sheet_index` — 0-based position in the workbook
- `.is_hidden`   — `True` when the sheet is hidden
- `.elements`    — list of `TableElement` (one per sheet) and any `ImageElement`

The `TableElement.data` is a 2-D list of strings ready for downstream
normalisation or LLM consumption.

```python
def _make_ws(name, rows, state="visible"):
    ws = MagicMock()
    ws.sheet_state = state
    ws.title = name
    ws._images = []
    mock_rows = []
    for row_data in rows:
        mock_rows.append([MagicMock(value=v) for v in row_data])
    ws.iter_rows.return_value = mock_rows
    return ws


with patch("sayou.document.parser.excel_parser.openpyxl") as mock_opx:
    sales_ws = _make_ws(
        "Sales",
        [
            ["Month", "Revenue", "Units", "Region"],
            ["Jan", "120000", "240", "APAC"],
            ["Feb", "135000", "270", "APAC"],
            ["Mar", "98000", "196", "EMEA"],
        ],
    )
    config_ws = _make_ws(
        "Config",
        [
            ["Key", "Value"],
            ["currency", "USD"],
            ["fiscal_year", "2024"],
        ],
    )
    archive_ws = _make_ws("Archive_2023", [["Date", "Amount"]], state="hidden")

    wb = MagicMock()
    wb.sheetnames = ["Sales", "Config", "Archive_2023"]
    sheets = {"Sales": sales_ws, "Config": config_ws, "Archive_2023": archive_ws}
    wb.__getitem__ = lambda self, k: sheets[k]
    mock_opx.load_workbook.return_value = wb

    doc = DocumentPipeline.process(b"PK\x03\x04", "report.xlsx")

print("=== Parse a Workbook ===")
print(f"  doc_type    : {doc.doc_type}")
print(f"  sheet_count : {doc.page_count}")
for sheet in doc.pages:
    assert isinstance(sheet, Sheet)
    tbl = next((e for e in sheet.elements if isinstance(e, TableElement)), None)
    rows = len(tbl.data) if tbl else 0
    cols = len(tbl.data[0]) if tbl and tbl.data else 0
    print(f"  [{sheet.sheet_name:15s}] hidden={sheet.is_hidden}  {rows}×{cols}")
```

## Inspect Table Data

`TableElement.data` is indexed as `data[row][col]`.
`TableElement.caption` contains the sheet name.

```python
sales_sheet = next(s for s in doc.pages if s.sheet_name == "Sales")
tbl = next(e for e in sales_sheet.elements if isinstance(e, TableElement))

print("\n=== Inspect Table Data ===")
print(f"  Caption  : {tbl.caption}")
print(f"  Header   : {tbl.data[0]}")
for row in tbl.data[1:]:
    print(f"  Row      : {row}")
```

## Skip Hidden Sheets

Pass `skip_hidden=True` to exclude hidden worksheets from the output.

```python
with patch("sayou.document.parser.excel_parser.openpyxl") as mock_opx:
    wb2 = MagicMock()
    wb2.sheetnames = ["Sales", "Config", "Archive_2023"]
    wb2.__getitem__ = lambda self, k: sheets[k]
    mock_opx.load_workbook.return_value = wb2

    doc_visible = DocumentPipeline.process(
        b"PK\x03\x04", "report.xlsx", skip_hidden=True
    )

print("\n=== Skip Hidden Sheets ===")
names = [s.sheet_name for s in doc_visible.pages]
print(f"  Visible sheets: {names}")
print(f"  Skipped hidden: {'Archive_2023' not in names}")
```

## Save Results

```python
output = doc.model_dump()
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nSaved Document to '{OUTPUT_FILE}'")
```