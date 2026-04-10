import io
import re
import struct
import zlib
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional, Tuple

try:
    import olefile
except ImportError:
    olefile = None

from sayou.core.registry import register_component

from ..interfaces.base_parser import BaseDocumentParser
from ..models import (
    BaseElement,
    Document,
    DocumentMetadata,
    ElementMetadata,
    ImageElement,
    Page,
    TableCell,
    TableElement,
    TextElement,
)

# ---------------------------------------------------------------------------
# HWP 5.0 binary constants
# ---------------------------------------------------------------------------

# BodyText record tag IDs
_TAG_PARA_HEADER = 66  # 0x42 — paragraph properties
_TAG_PARA_TEXT = 67  # 0x43 — paragraph text (UTF-16 LE)
_TAG_PARA_CHAR_SHAPE = 68  # 0x44 — character shape (font size, …)
_TAG_CTRL_HEADER = 71  # 0x47 — inline control start
_TAG_CTRL_END = 72  # 0x48 — inline control end (cell boundary in tables)
_TAG_LIST_HEADER = 74  # 0x4A — list container
_TAG_TABLE_DEF = 77  # 0x4D — table definition (num_rows, num_cols)

# DocInfo record tag IDs
_TAG_STYLE = 3855  # 0x0F0F
_TAG_BINARY_DATA = 3844  # 0x0F04

# ---------------------------------------------------------------------------
# Control IDs — HWP stores ctrl_id as LE UINT32, so the 4 bytes in the file
# are the ASCII name in REVERSE order:
#   "tbl " = [0x74,0x62,0x6C,0x20] → stored as [0x20,0x6C,0x62,0x74] = b" lbt"
#   "gso " = [0x67,0x73,0x6F,0x20] → stored as [0x20,0x6F,0x73,0x67] = b" osg"
# ---------------------------------------------------------------------------
_CTRL_TABLE = b" lbt"  # "tbl " reversed
_CTRL_GSO = b" osg"  # "gso " reversed
_CTRL_PICTURE = b"lle$"  # "$ell" reversed — legacy inline picture

# Additional known image ctrl_ids (LE byte order in file)
_IMAGE_CTRL_IDS = {
    b"lle$",  # "$ell" — inline picture
    b" osg",  # "gso " — general shape object (may be image)
    b"pgnp",  # page background image variant
    b"pngp",  # PNG picture / stamp control seen in practice
    b" gni",  # "ing " — another inline graphic variant
}

# Non-table inline controls that contain text
_CTRL_HEADER_AREA = b"daeh"  # "head" reversed — 머리말
_CTRL_FOOTER_AREA = b"toof"  # "foot" reversed — 꼬리말
_CTRL_FOOTNOTE = b"  nf"  # "fn  " reversed — 각주
_CTRL_ENDNOTE = b"  ne"  # "en  " reversed — 미주
_CTRL_TEXTBOX = b" xbt"  # "tbx " reversed — 글상자 (GSO 내부)

# Ctrl IDs whose nested PARA_TEXT should be collected as text
_TEXT_CTRL_IDS = {
    _CTRL_HEADER_AREA: "header",
    _CTRL_FOOTER_AREA: "footer",
    _CTRL_FOOTNOTE: "footnote",
    _CTRL_ENDNOTE: "endnote",
    _CTRL_GSO: "textbox",  # may be image or textbox; text check at flush
    _CTRL_TEXTBOX: "textbox",
}

_OLE_MAGIC = b"\xd0\xcf\x11\xe0"

# Minimum text length to keep (noise filter)
_MIN_TEXT_LEN = 2

# Style name prefixes
_HEADING_PREFIXES = ("제목", "Heading", "heading")
_LIST_PREFIXES = ("목록", "글머리", "번호", "List", "Bullet", "Number")

# Font size threshold for heading detection via CHAR_SHAPE (unit: 1/100 pt)
_HEADING_FONT_SIZE_MIN = 1400  # 14 pt


# ---------------------------------------------------------------------------
# Internal data structures
# ---------------------------------------------------------------------------


@dataclass
class _StyleInfo:
    style_id: int
    name: str
    type: int
    heading_lvl: int
    is_list: bool


@dataclass
class _ParaInfo:
    style_id: int = 0
    level: int = 0
    char_font_size: int = 0  # kept for future DocInfo cross-ref
    ctrl_mask: int = 0
    bold: bool = False


from typing import NamedTuple


class _CellData(NamedTuple):
    col: int  # 0-based column position (CTRL_END bytes 8-9)
    colspan: int  # columns spanned (CTRL_END bytes 12-13)
    rowspan: int  # rows spanned (CTRL_END bytes 14-15)
    text: str


@dataclass
class _TableContext:
    """
    Accumulates one table using cell coordinate data from CTRL_END bytes 8-15.

    Each CTRL_END at cell level carries:
      bytes 8-9  : col_start  (uint16 LE, 0-based)
      bytes 10-11: row_start  (uint16 LE, 1-based)
      bytes 12-13: colspan    (uint16 LE)
      bytes 14-15: rowspan    (uint16 LE)

    Cells are accumulated in ``pending_cells`` and the 2D grid is built at
    flush time by placing each cell's text at (row-1, col) and leaving
    spanned positions as empty strings.
    """

    ctrl_level: int = 0
    num_rows: int = 0  # from TABLE_DEF
    num_cols: int = 0  # from TABLE_DEF
    cells_per_row: List[int] = field(default_factory=list)  # visual row sizes
    elem_id: str = ""
    page_num: int = 1
    got_table_def: bool = False
    header_closed: bool = False

    # Cell accumulation (sequential, grouped by cells_per_row)
    current_cell_parts: List[str] = field(default_factory=list)
    pending_cells: List[_CellData] = field(default_factory=list)

    def end_cell(self, col: int, colspan: int, rowspan: int) -> None:
        """Finalize the current cell."""
        text = " ".join(self.current_cell_parts).strip()
        self.current_cell_parts.clear()
        self.pending_cells.append(_CellData(col, colspan, rowspan, text))

    def build_cells_grid(self) -> List[List["TableCell"]]:
        """
        Build a rectangular 2D grid using cells_per_row for row grouping
        and stream order for column placement within each row.

        Within each row group, cells appear in left-to-right visual order
        (stream order).  Rowspan: origin cell marks subsequent rows at the
        same cursor column as covered.
        """
        if not self.pending_cells:
            return []

        n_cols = self.num_cols or 1
        cpr = self.cells_per_row

        # Group cells into visual rows using cells_per_row
        visual_rows: List[List[_CellData]] = []
        idx = 0
        for count in cpr:
            if idx >= len(self.pending_cells):
                break
            visual_rows.append(self.pending_cells[idx : idx + count])
            idx += count
        if idx < len(self.pending_cells):
            visual_rows.append(self.pending_cells[idx:])

        n_rows = len(visual_rows)
        grid: List[List[TableCell]] = [
            [TableCell(text="", row_span=1, col_span=1) for _ in range(n_cols)]
            for _ in range(n_rows)
        ]
        # covered[(r, c)] = True → occupied by a rowspan origin above
        covered: dict = {}

        # placed[(r, c)] = True once a cell has been explicitly written to that slot
        placed: dict = {}

        for r_idx, row_cells in enumerate(visual_rows):
            for cell in row_cells:
                c = cell.col
                if c >= n_cols:
                    continue
                if covered.get((r_idx, c)):
                    continue  # occupied by rowspan from a previous row
                if placed.get((r_idx, c)):
                    continue  # already written in this row (stream group mix)

                rs = max(1, cell.rowspan)
                cs = max(1, cell.colspan)

                grid[r_idx][c] = TableCell(
                    text=cell.text,
                    row_span=rs,
                    col_span=cs,
                    is_header=(r_idx == 0),
                )
                placed[(r_idx, c)] = True

                # Mark all spanned positions as covered
                for dr in range(rs):
                    for dc in range(cs):
                        if dr == 0 and dc == 0:
                            continue
                        sr, sc = r_idx + dr, c + dc
                        if 0 <= sr < n_rows and 0 <= sc < n_cols:
                            covered[(sr, sc)] = True
                            grid[sr][sc] = TableCell(
                                text="", row_span=0, col_span=0, is_header=False
                            )

        return grid

    def build_grid(self) -> List[List[str]]:
        """Plain 2D string grid derived from build_cells_grid (LLM-friendly)."""
        cells = self.build_cells_grid()
        return [[tc.text for tc in row] for row in cells]


@dataclass
class _InlineCtx:
    """
    State for non-table inline controls that contain text.

    Covers: 머리말(header), 꼬리말(footer), 각주(footnote),
            미주(endnote), 글상자(textbox/GSO).

    For GSO controls: ``record_bytes`` holds the original CTRL_HEADER
    payload so that _flush_inline() can attempt BinData image extraction
    as a fallback when no nested text was collected (i.e., the GSO is a
    pure image rather than a text box).
    """

    ctrl_type: str  # semantic label
    ctrl_level: int  # record level of the opening CTRL_HEADER
    texts: List[str] = field(default_factory=list)
    record_bytes: Optional[bytes] = None  # original CTRL_HEADER payload (GSO only)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


@register_component("parser")
class HwpParser(BaseDocumentParser):
    """
    Parser for Hancom Word Processor (.hwp 5.0) documents.

    Key implementation notes
    ────────────────────────
    ctrl_id byte order
        HWP stores control IDs as LE UINT32 integers, so the 4 bytes in the
        file are the ASCII name in REVERSE order.  ``"tbl "`` appears in the
        file as ``b" lbt"`` (hex: 20 6c 62 74).

    Table cell boundaries
        Cells are delimited by ``CTRL_END`` (tag 72) records at
        ``ctrl_level + 1``, NOT by ``LIST_HEADER`` (tag 74).
        ``HWPTAG_TABLE`` (tag 77) carries the column count used to group
        cells into rows.

    Produces
    ────────
    TextElement  — paragraphs with ``semantic_type`` (heading / list_item /
                   paragraph).  Consecutive same-style paragraphs are merged.
    TableElement — rows and cells derived from the CTRL_END stream.
    ImageElement — from ``BinData/BIN*.xxx`` OLE streams with optional OCR.

    Requires::

        pip install olefile
    """

    component_name = "HwpParser"
    SUPPORTED_TYPES = [".hwp"]

    # ------------------------------------------------------------------
    # can_handle
    # ------------------------------------------------------------------

    @classmethod
    def can_handle(cls, file_bytes: bytes, file_name: str) -> float:
        ext_ok = file_name.lower().endswith(".hwp")
        sig_ok = file_bytes[:4] == _OLE_MAGIC
        if sig_ok and ext_ok:
            return 1.0
        if ext_ok:
            return 0.8
        return 0.0

    # ------------------------------------------------------------------
    # _do_parse
    # ------------------------------------------------------------------

    def _do_parse(self, file_bytes: bytes, file_name: str, **kwargs) -> Document:
        if olefile is None:
            raise ImportError(
                "The 'olefile' package is required. Install: pip install olefile"
            )

        try:
            ole = olefile.OleFileIO(io.BytesIO(file_bytes))
        except Exception as exc:
            raise ValueError(f"Cannot open HWP OLE container: {exc}") from exc

        if not ole.exists("FileHeader"):
            raise ValueError(f"'{file_name}' is not a valid HWP 5.0 document.")

        # 1. Style definitions
        styles: Dict[int, _StyleInfo] = {}
        if ole.exists("DocInfo"):
            try:
                styles = self._parse_docinfo_styles(ole)
            except Exception as exc:
                self._log(f"DocInfo style parsing failed: {exc}", level="warning")

        # 2. Embedded images
        bin_data: Dict[str, bytes] = {}
        try:
            bin_data = self._extract_bin_data(ole)
        except Exception as exc:
            self._log(f"BinData extraction failed: {exc}", level="warning")

        # 3. BodyText sections
        if not ole.exists("BodyText"):
            self._log(f"'{file_name}': BodyText not found.", level="warning")
            return self._empty_document(file_name)

        section_streams = sorted(dp for dp in ole.listdir() if dp[0] == "BodyText")

        all_elements: List[BaseElement] = []

        for sec_idx, dir_path in enumerate(section_streams):
            try:
                raw = ole.openstream(dir_path).read()
            except Exception as exc:
                self._log(f"Cannot read '{'/'.join(dir_path)}': {exc}", level="warning")
                continue
            if not raw:
                continue

            data = self._decompress(raw, "/".join(dir_path))
            elems = self._parse_section(
                data, sec_idx, styles, bin_data, file_name, **kwargs
            )
            all_elements.extend(elems)

        # Emit any BinData streams that were not matched by ctrl_id references.
        # This ensures no embedded images are silently dropped when an unknown
        # ctrl_id is used (e.g., stamp/seal images with non-standard IDs).
        referenced_keys = {
            e.id.split(":")[-1] if hasattr(e, "image_base64") else ""
            for e in all_elements
        }
        ocr_enabled = kwargs.get("ocr_enabled", True)
        for bin_idx, (key, raw_img) in enumerate(bin_data.items()):
            if not raw_img:
                continue
            # Skip if already emitted (check image_base64 content match is
            # expensive; instead track by checking if any ImageElement
            # references this key via raw_attributes)
            already_emitted = any(
                isinstance(e, ImageElement) and e.raw_attributes.get("bin_key") == key
                for e in all_elements
            )
            if already_emitted:
                continue
            ext = key[-3:].lower() if len(key) >= 3 else "png"
            eid = f"hwp:{file_name}:bin:{key}"
            img_elem = self._process_image_data(
                image_bytes=raw_img,
                img_format=ext,
                elem_id=eid,
                page_num=1,
                ocr_enabled=ocr_enabled,
            )
            img_elem.raw_attributes["bin_key"] = key
            img_elem.raw_attributes["source"] = "unmatched_bindata"
            img_elem.raw_attributes["section_context"] = next(
                (
                    e.text
                    for e in reversed(all_elements)
                    if hasattr(e, "raw_attributes")
                    and e.raw_attributes.get("semantic_type") == "heading"
                ),
                "",
            )
            all_elements.append(img_elem)

        page = Page(
            page_num=1,
            elements=all_elements,
            header_elements=[],
            footer_elements=[],
            text="\n".join(e.text for e in all_elements if e.text),
        )

        return Document(
            file_name=file_name,
            file_id=file_name,
            doc_type="word",
            metadata=DocumentMetadata(source_path=file_name),
            page_count=max(1, len(section_streams)),
            pages=[page],
        )

    # ------------------------------------------------------------------
    # DocInfo
    # ------------------------------------------------------------------

    def _parse_docinfo_styles(self, ole) -> Dict[int, _StyleInfo]:
        raw = ole.openstream("DocInfo").read()
        data = self._decompress(raw, "DocInfo")
        styles: Dict[int, _StyleInfo] = {}
        idx = 0
        for tag_id, _, record in self._walk_records(data):
            if tag_id != _TAG_STYLE or len(record) < 11:
                continue
            name = self._decode_null_term_utf16(record[10:])
            heading = self._heading_level_from_name(name)
            is_list = any(name.startswith(p) for p in _LIST_PREFIXES)
            styles[idx] = _StyleInfo(
                style_id=idx,
                name=name,
                type=record[0],
                heading_lvl=heading,
                is_list=is_list,
            )
            idx += 1
        return styles

    @staticmethod
    def _heading_level_from_name(name: str) -> int:
        for prefix in _HEADING_PREFIXES:
            if name.startswith(prefix):
                trailing = name[len(prefix) :].strip()
                if trailing and trailing[0].isdigit():
                    return min(int(trailing[0]), 6)
        return 0

    @staticmethod
    def _decode_null_term_utf16(data: bytes) -> str:
        decoded = data.decode("utf-16-le", errors="ignore")
        null_pos = decoded.find("\x00")
        return decoded[:null_pos] if null_pos >= 0 else decoded

    # ------------------------------------------------------------------
    # BinData
    # ------------------------------------------------------------------

    def _extract_bin_data(self, ole) -> Dict[str, bytes]:
        """Extract BinData, decompressing with raw deflate (HWP's encoding)."""
        result: Dict[str, bytes] = {}
        if not ole.exists("BinData"):
            return result
        for dp in ole.listdir():
            if dp[0] != "BinData" or len(dp) < 2:
                continue
            key = dp[1].split(".")[0]
            try:
                raw = ole.openstream(dp).read()
                if not raw:
                    continue
                decompressed = None
                for wbits in (-15, 15):
                    try:
                        decompressed = zlib.decompress(raw, wbits)
                        break
                    except zlib.error:
                        pass
                result[key] = decompressed if decompressed is not None else raw
            except Exception as exc:
                self._log(f"BinData '{dp[1]}': {exc}", level="debug")
        return result

    # ------------------------------------------------------------------
    # Section parsing — state machine
    # ------------------------------------------------------------------

    def _parse_section(
        self,
        data: bytes,
        sec_idx: int,
        styles: Dict[int, _StyleInfo],
        bin_data: Dict[str, bytes],
        file_name: str,
        **kwargs,
    ) -> List[BaseElement]:
        """
        Walk a decompressed BodyText section.

        Table detection
        ───────────────
        - ``CTRL_HEADER b" lbt"`` (= "tbl " in LE byte order) → table start
        - ``HWPTAG_TABLE`` (tag 77) immediately after → read num_cols
        - ``CTRL_END`` at ``ctrl_level + 1``     → cell boundary
        - ``PARA_HEADER`` at level ≤ ctrl_level  → table end
        """
        elements: List[BaseElement] = []
        para_info = _ParaInfo()
        para_texts: List[str] = []
        table_stack: List[_TableContext] = []  # stack for nested tables
        inline_stack: List[_InlineCtx] = []  # stack for header/footer/footnote/textbox
        elem_ctr = 0
        ocr_enabled = kwargs.get("ocr_enabled", True)
        current_heading_text: str = ""

        def _next_id(prefix: str) -> str:
            nonlocal elem_ctr
            eid = f"hwp:{file_name}:s{sec_idx}:{prefix}{elem_ctr}"
            elem_ctr += 1
            return eid

        def _cur() -> Optional[_TableContext]:
            return table_stack[-1] if table_stack else None

        def _cur_inline() -> Optional[_InlineCtx]:
            return inline_stack[-1] if inline_stack else None

        # ── _flush_para ────────────────────────────────────────────────
        def _flush_para() -> None:
            nonlocal current_heading_text
            text = " ".join(para_texts).strip()
            para_texts.clear()
            if len(text) < _MIN_TEXT_LEN:
                return

            eid = _next_id("para")
            style = styles.get(para_info.style_id)

            if style and style.is_list:
                stype, heading = "list_item", 0
            else:
                heading = style.heading_lvl if style else 0
                if not heading and para_info.level:
                    heading = para_info.level
                if not heading and para_info.char_font_size >= _HEADING_FONT_SIZE_MIN:
                    fs = para_info.char_font_size
                    if fs >= 2800:
                        heading = 1
                    elif fs >= 2000:
                        heading = 2
                    elif fs >= 1600:
                        heading = 3
                    else:
                        heading = 4
                stype = "heading" if heading else "paragraph"

            raw_attrs: dict = {
                "style_id": para_info.style_id,
                "style_name": style.name if style else "",
                "bold": para_info.bold,
            }
            if stype == "heading":
                current_heading_text = text
                raw_attrs.update({"semantic_type": "heading", "heading_level": heading})
            else:
                raw_attrs["semantic_type"] = stype

            elements.append(
                TextElement(
                    id=eid,
                    type="text",
                    text=text,
                    meta=ElementMetadata(page_num=1, id=eid),
                    raw_attributes=raw_attrs,
                )
            )

        # ── _flush_table ───────────────────────────────────────────────
        def _flush_table() -> None:
            """Emit the innermost TableElement using coordinate-based grid."""
            ctx = _cur()
            if ctx is None:
                return
            if ctx.current_cell_parts:
                ctx.end_cell(col=0, colspan=1, rowspan=1)
            cells_grid = ctx.build_cells_grid()
            eid = ctx.elem_id
            if cells_grid:
                data_grid = [[tc.text for tc in row] for row in cells_grid]
                elements.append(
                    TableElement(
                        id=eid,
                        type="table",
                        data=data_grid,
                        cells=cells_grid,
                        meta=ElementMetadata(page_num=ctx.page_num, id=eid),
                    )
                )
            table_stack.pop()
            parent = _cur()
            if parent is not None and cells_grid:
                parent.current_cell_parts.append(f"[table:{eid}]")

        # ── _flush_inline ──────────────────────────────────────────────
        def _flush_inline() -> None:
            """
            Emit the collected inline control content and pop the stack.

            Text collected → TextElement with ``semantic_type`` matching the
            control type (header, footer, footnote, endnote, textbox).

            No text collected AND ctrl_type == "textbox" → attempt BinData
            image extraction from the stored record bytes (GSO image fallback).
            If that also fails, the control is silently discarded.
            """
            ctx = _cur_inline()
            if ctx is None:
                return
            text_content = " ".join(ctx.texts).strip()
            inline_stack.pop()

            if text_content:
                eid = _next_id(ctx.ctrl_type)
                elements.append(
                    TextElement(
                        id=eid,
                        type="text",
                        text=text_content,
                        meta=ElementMetadata(page_num=1, id=eid),
                        raw_attributes={"semantic_type": ctx.ctrl_type},
                    )
                )
                return

            # No text — for GSO controls, try extracting a BinData image
            if ctx.ctrl_type == "textbox" and ctx.record_bytes is not None:
                img_key = self._extract_bin_ref(ctx.record_bytes)
                img_raw = bin_data.get(img_key) if img_key else None
                if img_raw:
                    eid = _next_id("img")
                    ext = (img_key[-3:].lower() if img_key else "png") or "png"
                    img_elem = self._process_image_data(
                        image_bytes=img_raw,
                        img_format=ext,
                        elem_id=eid,
                        page_num=1,
                        ocr_enabled=ocr_enabled,
                    )
                    img_elem.raw_attributes["section_context"] = current_heading_text
                    elements.append(img_elem)
            # Otherwise silently discard (empty control)

        # ── Record walk ────────────────────────────────────────────────
        for tag_id, level, record in self._walk_records(data):

            # ── PARA_HEADER ───────────────────────────────────────────
            if tag_id == _TAG_PARA_HEADER:
                # Check inline controls first (footnote/header/textbox end)
                ic = _cur_inline()
                if ic is not None and level <= ic.ctrl_level:
                    _flush_inline()

                ctx = _cur()
                if ctx is not None:
                    if level <= ctx.ctrl_level:
                        # Returned to the level of the enclosing context → table ended
                        _flush_table()
                        if not table_stack:
                            _flush_para()
                    # else: paragraph inside a cell — keep accumulating
                else:
                    _flush_para()
                para_info = self._parse_para_header(record)
                para_info.char_font_size = 0
                para_info.bold = False

            # ── PARA_CHAR_SHAPE ───────────────────────────────────────
            elif tag_id == _TAG_PARA_CHAR_SHAPE and not table_stack:
                if len(record) >= 2:
                    para_info.char_font_size = int.from_bytes(record[0:2], "little")
                if len(record) >= 8:
                    attr = int.from_bytes(record[4:8], "little")
                    para_info.bold = bool(attr & 0x01)

            # ── PARA_TEXT ─────────────────────────────────────────────
            elif tag_id == _TAG_PARA_TEXT:
                text = self._decode_para_text(record)
                if not text:
                    continue
                ic = _cur_inline()
                if ic is not None:
                    ic.texts.append(text)
                elif _cur() is not None:
                    _cur().current_cell_parts.append(text)
                else:
                    para_texts.append(text)

            # ── CTRL_HEADER ───────────────────────────────────────────
            elif tag_id == _TAG_CTRL_HEADER and len(record) >= 4:
                ctrl_id = record[:4]

                if ctrl_id == _CTRL_TABLE:
                    if not table_stack:
                        _flush_para()
                    # Push a new context — handles both top-level and nested tables
                    table_stack.append(
                        _TableContext(
                            ctrl_level=level,
                            elem_id=_next_id("table"),
                            page_num=1,
                        )
                    )

                elif ctrl_id in _TEXT_CTRL_IDS:
                    # Non-table inline control that may contain text.
                    # Store record bytes for GSO so _flush_inline can attempt
                    # BinData image extraction when no text is found.
                    inline_stack.append(
                        _InlineCtx(
                            ctrl_type=_TEXT_CTRL_IDS[ctrl_id],
                            ctrl_level=level,
                            record_bytes=record if ctrl_id == _CTRL_GSO else None,
                        )
                    )

                elif ctrl_id in _IMAGE_CTRL_IDS and ctrl_id not in _TEXT_CTRL_IDS:
                    # Known image control — extract BinData reference directly
                    img_key = self._extract_bin_ref(record)
                    img_raw = bin_data.get(img_key) if img_key else None
                    if img_raw:
                        eid = _next_id("img")
                        ext = (img_key[-3:].lower() if img_key else "png") or "png"
                        img_elem = self._process_image_data(
                            image_bytes=img_raw,
                            img_format=ext,
                            elem_id=eid,
                            page_num=1,
                            ocr_enabled=ocr_enabled,
                        )
                        img_elem.raw_attributes["bin_key"] = img_key
                        img_elem.raw_attributes["section_context"] = (
                            current_heading_text
                        )
                        elements.append(img_elem)

            # ── HWPTAG_TABLE (tag 77) — table definition ──────────────
            elif tag_id == _TAG_TABLE_DEF:
                ctx = _cur()
                if ctx is not None and not ctx.got_table_def and len(record) >= 8:
                    n_rows = int.from_bytes(record[4:6], "little")
                    ctx.num_rows = n_rows
                    ctx.num_cols = int.from_bytes(record[6:8], "little")
                    # bytes 18+ : n_rows × uint16 — cells per visual row
                    if len(record) >= 18 + n_rows * 2:
                        cpr, off = [], 18
                        for _ in range(n_rows):
                            cpr.append(int.from_bytes(record[off : off + 2], "little"))
                            off += 2
                        ctx.cells_per_row = cpr
                    ctx.got_table_def = True

            # ── CTRL_END — cell boundary ──────────────────────────────
            elif tag_id == _TAG_CTRL_END:
                ctx = _cur()
                if ctx is not None:
                    cell_level = ctx.ctrl_level + 1

                    if level == cell_level:
                        if not ctx.header_closed:
                            ctx.header_closed = True
                        else:
                            col = (
                                int.from_bytes(record[8:10], "little")
                                if len(record) >= 10
                                else 0
                            )
                            colspan = max(
                                1,
                                (
                                    int.from_bytes(record[12:14], "little")
                                    if len(record) >= 14
                                    else 1
                                ),
                            )
                            rowspan = max(
                                1,
                                (
                                    int.from_bytes(record[14:16], "little")
                                    if len(record) >= 16
                                    else 1
                                ),
                            )
                            ctx.end_cell(col=col, colspan=colspan, rowspan=rowspan)

                    elif len(table_stack) >= 2:
                        for depth in range(len(table_stack) - 2, -1, -1):
                            ancestor = table_stack[depth]
                            if level == ancestor.ctrl_level + 1:
                                while len(table_stack) > depth + 1:
                                    _flush_table()
                                anc = _cur()
                                if anc is not None:
                                    if not anc.header_closed:
                                        anc.header_closed = True
                                    else:
                                        col = (
                                            int.from_bytes(record[8:10], "little")
                                            if len(record) >= 10
                                            else 0
                                        )
                                        colspan = max(
                                            1,
                                            (
                                                int.from_bytes(record[12:14], "little")
                                                if len(record) >= 14
                                                else 1
                                            ),
                                        )
                                        rowspan = max(
                                            1,
                                            (
                                                int.from_bytes(record[14:16], "little")
                                                if len(record) >= 16
                                                else 1
                                            ),
                                        )
                                        anc.end_cell(
                                            col=col, colspan=colspan, rowspan=rowspan
                                        )
                                break

        # ── Flush remaining state ──────────────────────────────────────
        while inline_stack:
            _flush_inline()
        while table_stack:
            _flush_table()
        _flush_para()

        return elements

    # ------------------------------------------------------------------
    # Record-level helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_para_header(data: bytes) -> _ParaInfo:
        """
        HWPTAG_PARA_HEADER byte layout:
          0–3   UINT32  nChar
          4–7   UINT32  controlMask
          8–9   UINT16  paraShapeId
          10    UINT8   styleId
          11    UINT8   level  (0=body, 1–7=heading)
        """
        if len(data) < 12:
            return _ParaInfo()
        return _ParaInfo(
            style_id=data[10],
            level=data[11],
            ctrl_mask=int.from_bytes(data[4:8], "little"),
        )

    @staticmethod
    def _decode_para_text(data: bytes) -> str:
        """
        Decode HWPTAG_PARA_TEXT payload (UTF-16 LE).

        HWP embeds inline object anchors (0x0002) and field markers
        (0x000B, 0x000C) whose surrounding bytes are binary reference data.
        When decoded as UTF-16 LE those bytes produce spurious CJK characters
        (e.g. 汤捯, 氠瑢).  We split on the anchor/field chars and strip
        leading CJK Unified Ideograph characters from each segment.
        """
        decoded = data.decode("utf-16-le", errors="ignore")

        result_parts = []
        for segment in re.split(r"[\x02\x0b\x0c]", decoded):
            # Strip control codes (keep tab)
            clean = "".join(ch for ch in segment if ord(ch) >= 0x20 or ch == "\t")
            if not clean:
                continue
            # Strip leading CJK Unified Ideograph chars — binary object-ref
            # data that bleeds past the split boundary as high UTF-16 pairs
            i = 0
            while i < len(clean) and "\u4e00" <= clean[i] <= "\u9fff":
                i += 1
            clean = clean[i:].strip()
            if clean:
                result_parts.append(clean)

        return " ".join(result_parts).strip()

    @staticmethod
    def _extract_bin_ref(ctrl_data: bytes) -> Optional[str]:
        """Extract BinData key from GSO/picture ctrl record."""
        try:
            if len(ctrl_data) >= 6:
                bin_id = struct.unpack_from("<H", ctrl_data, 4)[0]
                if bin_id:
                    return f"BIN{bin_id:04d}"
        except Exception:
            pass
        return None

    @staticmethod
    def _walk_records(data: bytes) -> Iterator[Tuple[int, int, bytes]]:
        """
        Walk a flat HWP binary record stream.

        Record header (4 bytes LE UINT32):
          bits  0– 9 : tag ID
          bits 10–19 : level (nesting depth)
          bits 20–31 : size  (0xFFF → next 4 bytes hold actual size)

        Yields ``(tag_id, level, record_data)``.
        """
        offset = 0
        length = len(data)
        while offset < length:
            if offset + 4 > length:
                break
            header = int.from_bytes(data[offset : offset + 4], "little")
            offset += 4
            tag_id = header & 0x3FF
            level = (header >> 10) & 0x3FF
            size = (header >> 20) & 0xFFF
            if size == 0xFFF:
                if offset + 4 > length:
                    break
                size = int.from_bytes(data[offset : offset + 4], "little")
                offset += 4
            if offset + size > length:
                break
            yield tag_id, level, data[offset : offset + size]
            offset += size

    # ------------------------------------------------------------------
    # Compression / utility
    # ------------------------------------------------------------------

    def _decompress(self, data: bytes, stream_name: str) -> bytes:
        for wbits in (-15, 15):
            try:
                return zlib.decompress(data, wbits)
            except zlib.error:
                pass
        self._log(
            f"Stream '{stream_name}': decompression failed — treating as raw.",
            level="debug",
        )
        return data

    @staticmethod
    def _empty_document(file_name: str) -> Document:
        return Document(
            file_name=file_name,
            file_id=file_name,
            doc_type="word",
            page_count=0,
            pages=[],
        )
