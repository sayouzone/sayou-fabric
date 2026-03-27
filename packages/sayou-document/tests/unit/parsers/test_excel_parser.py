"""
Unit tests for ExcelParser.

Patches openpyxl so tests run without the package installed.
"""

from __future__ import annotations

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from sayou.document.models import Document, Sheet, TableElement
from sayou.document.parser.excel_parser import ExcelParser


def _make_workbook(sheets: list[dict]):
    """
    sheets: list of {"name": str, "rows": list[list], "state": "visible"|"hidden"}
    """
    wb = MagicMock()
    mock_sheets = {}
    for s in sheets:
        ws = MagicMock()
        ws.sheet_state = s.get("state", "visible")
        ws.title = s["name"]
        ws._images = []

        rows = s.get("rows", [])
        mock_rows = []
        for row_data in rows:
            mock_row = []
            for cell_val in row_data:
                cell = MagicMock()
                cell.value = cell_val
                mock_row.append(cell)
            mock_rows.append(mock_row)
        ws.iter_rows.return_value = mock_rows
        mock_sheets[s["name"]] = ws

    wb.sheetnames = [s["name"] for s in sheets]
    wb.__getitem__ = lambda self, k: mock_sheets[k]
    return wb


# ---------------------------------------------------------------------------
# can_handle
# ---------------------------------------------------------------------------


class TestExcelParserCanHandle:
    def test_pk_with_xlsx_extension(self):
        assert ExcelParser.can_handle(b"PK\x03\x04", "data.xlsx") == 1.0

    def test_ole_signature(self):
        assert ExcelParser.can_handle(b"\xd0\xcf\x11\xe0extra", "old.xls") == 1.0

    def test_extension_fallback(self):
        assert ExcelParser.can_handle(b"\x00\x00", "data.xlsm") == 0.8

    def test_non_excel_returns_0(self):
        assert ExcelParser.can_handle(b"%PDF", "report.pdf") == 0.0


# ---------------------------------------------------------------------------
# _do_parse
# ---------------------------------------------------------------------------


class TestExcelParserParse:
    @patch("sayou.document.parser.excel_parser.openpyxl")
    def test_returns_document(self, mock_openpyxl):
        wb = _make_workbook([{"name": "Sheet1", "rows": [["A", "B"], [1, 2]]}])
        mock_openpyxl.load_workbook.return_value = wb

        parser = ExcelParser()
        doc = parser._do_parse(b"PK\x03\x04", "data.xlsx")

        assert isinstance(doc, Document)
        assert doc.doc_type == "sheet"

    @patch("sayou.document.parser.excel_parser.openpyxl")
    def test_each_sheet_becomes_a_page(self, mock_openpyxl):
        wb = _make_workbook(
            [
                {"name": "Alpha", "rows": [["x"], [1]]},
                {"name": "Beta", "rows": [["y"], [2]]},
            ]
        )
        mock_openpyxl.load_workbook.return_value = wb

        parser = ExcelParser()
        doc = parser._do_parse(b"PK", "multi.xlsx")

        assert doc.page_count == 2
        names = [p.sheet_name for p in doc.pages if isinstance(p, Sheet)]
        assert "Alpha" in names
        assert "Beta" in names

    @patch("sayou.document.parser.excel_parser.openpyxl")
    def test_table_element_data(self, mock_openpyxl):
        rows = [["Name", "Score"], ["Alice", 95], ["Bob", 80]]
        wb = _make_workbook([{"name": "Data", "rows": rows}])
        mock_openpyxl.load_workbook.return_value = wb

        parser = ExcelParser()
        doc = parser._do_parse(b"PK", "data.xlsx")

        sheet = doc.pages[0]
        tbl_elems = [e for e in sheet.elements if isinstance(e, TableElement)]
        assert len(tbl_elems) == 1
        assert tbl_elems[0].data[0] == ["Name", "Score"]
        assert tbl_elems[0].data[1][0] == "Alice"

    @patch("sayou.document.parser.excel_parser.openpyxl")
    def test_hidden_sheet_skipped_when_flag_set(self, mock_openpyxl):
        wb = _make_workbook(
            [
                {"name": "Visible", "rows": [["v"]]},
                {"name": "Hidden", "rows": [["h"]], "state": "hidden"},
            ]
        )
        mock_openpyxl.load_workbook.return_value = wb

        parser = ExcelParser()
        doc = parser._do_parse(b"PK", "data.xlsx", skip_hidden=True)

        assert doc.page_count == 1
        assert doc.pages[0].sheet_name == "Visible"

    @patch("sayou.document.parser.excel_parser.openpyxl")
    def test_hidden_sheet_included_by_default(self, mock_openpyxl):
        wb = _make_workbook(
            [
                {"name": "Visible", "rows": [["v"]]},
                {"name": "Hidden", "rows": [["h"]], "state": "hidden"},
            ]
        )
        mock_openpyxl.load_workbook.return_value = wb

        parser = ExcelParser()
        doc = parser._do_parse(b"PK", "data.xlsx")

        assert doc.page_count == 2

    @patch("sayou.document.parser.excel_parser.openpyxl")
    def test_empty_rows_excluded(self, mock_openpyxl):
        """Rows where all cells are None should not appear in the table."""
        rows = [["Name", "Score"], [None, None], ["Alice", 95]]
        wb = _make_workbook([{"name": "Sheet1", "rows": rows}])
        mock_openpyxl.load_workbook.return_value = wb

        parser = ExcelParser()
        doc = parser._do_parse(b"PK", "data.xlsx")

        tbl = [e for e in doc.pages[0].elements if isinstance(e, TableElement)][0]
        # Empty row stripped — only header + Alice row
        assert len(tbl.data) == 2
