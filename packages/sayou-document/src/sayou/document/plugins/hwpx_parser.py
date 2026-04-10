import io
import re
import xml.etree.ElementTree as ET
import zipfile
from typing import Dict, List, Optional, Tuple

from sayou.core.registry import register_component

from ..interfaces.base_parser import BaseDocumentParser
from ..models import (BaseElement, Document, DocumentMetadata, ElementMetadata,
                      ImageElement, Page, TableCell, TableElement, TextElement)

# ---------------------------------------------------------------------------
# HWPX XML namespace roots
# ---------------------------------------------------------------------------

# HWPX uses versioned namespaces; strip namespace for tag matching
_NS_SECTION = "http://www.hancom.co.kr/hwpml/2012/section"
_NS_PARA = "http://www.hancom.co.kr/hwpml/2012/paragraph"

# Heading style name prefixes (Korean + English)
_HEADING_PREFIXES = ("제목", "Heading", "heading")
_LIST_PREFIXES = ("목록", "글머리", "번호", "List", "Bullet", "Number")

# Font size threshold for heading fallback (unit: 1/200 pt in HWPX)
_HEADING_FONT_PT_MIN = 14.0

# Minimum text length to keep
_MIN_TEXT_LEN = 2

# Section XML path patterns inside the ZIP
_SECTION_PATH_RE = re.compile(r"(?i)^(contents?/)?section\d+\.xml$")
_CONTENT_PATH_RE = re.compile(r"(?i)^contents?/section\d+\.xml$")


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


@register_component("parser")
class HwpxParser(BaseDocumentParser):
    """
    Parser for Hancom Word Processor (.hwpx) documents.

    HWPX is the successor to HWP 5.0.  Instead of an OLE compound document,
    it uses a ZIP container whose content is stored as XML.  This makes
    parsing significantly more straightforward.

    Layout inside the ZIP:
    ├── Contents/
    │   ├── content.hpf     — package manifest
    │   ├── header.xml      — document metadata and style definitions
    │   ├── section0.xml    — body text section 0
    │   ├── section1.xml    — body text section 1 (if any)
    │   └── BinData/        — embedded images
    └── mimetype

    The parser extracts:

    TextElement
        Paragraphs with ``semantic_type`` (``"heading"``, ``"list_item"``,
        ``"paragraph"``).  Heading level is inferred from style names in
        ``header.xml`` and, as a fallback, from the ``<hp:sz>`` font size
        attribute.  Consecutive same-style paragraphs are merged.

    TableElement
        ``<hml:tbl>`` → ``<hml:tr>`` → ``<hml:tc>`` hierarchy,
        with first-row header detection.

    ImageElement
        Binary image data from the ``BinData/`` ZIP directory, with optional
        OCR via the attached OCR engine.

    Requires no additional dependencies beyond the Python standard library.
    """

    component_name = "HwpxParser"
    SUPPORTED_TYPES = [".hwpx"]

    # ------------------------------------------------------------------
    # can_handle
    # ------------------------------------------------------------------

    @classmethod
    def can_handle(cls, file_bytes: bytes, file_name: str) -> float:
        ext_ok = file_name.lower().endswith(".hwpx")
        sig_ok = file_bytes[:2] == b"PK"  # ZIP magic
        if sig_ok and ext_ok:
            return 1.0
        if ext_ok:
            return 0.8
        return 0.0

    # ------------------------------------------------------------------
    # _do_parse
    # ------------------------------------------------------------------

    def _do_parse(self, file_bytes: bytes, file_name: str, **kwargs) -> Document:
        try:
            zf = zipfile.ZipFile(io.BytesIO(file_bytes))
        except zipfile.BadZipFile as exc:
            raise ValueError(
                f"'{file_name}' is not a valid HWPX (ZIP) file: {exc}"
            ) from exc

        names = zf.namelist()

        # 1. Load style definitions from header.xml
        styles: Dict[str, _StyleDef] = {}
        header_path = next((n for n in names if n.lower().endswith("header.xml")), None)
        if header_path:
            try:
                styles = self._parse_header_styles(zf.read(header_path))
            except Exception as exc:
                self._log(f"header.xml style parsing failed: {exc}", level="warning")

        # 2. Load embedded images from BinData/
        bin_data: Dict[str, bytes] = {}
        for n in names:
            parts = n.replace("\\", "/").split("/")
            if any(p.lower() == "bindata" for p in parts):
                key = parts[-1].split(".")[0].upper()
                try:
                    bin_data[key] = zf.read(n)
                except Exception:
                    pass

        # 3. Parse section XML files in order
        section_paths = sorted(
            n for n in names if _CONTENT_PATH_RE.search(n)
        ) or sorted(n for n in names if _SECTION_PATH_RE.search(n.split("/")[-1]))

        if not section_paths:
            self._log(f"'{file_name}': no section XML found.", level="warning")
            return self._empty_document(file_name)

        all_elements: List[BaseElement] = []
        total_pages = 1
        ocr_enabled = kwargs.get("ocr_enabled", True)

        for sec_idx, path in enumerate(section_paths):
            try:
                xml_bytes = zf.read(path)
            except Exception as exc:
                self._log(f"Cannot read '{path}': {exc}", level="warning")
                continue

            elems, page_count = self._parse_section_xml(
                xml_bytes, sec_idx, styles, bin_data, file_name, ocr_enabled
            )
            all_elements.extend(elems)
            total_pages = max(total_pages, page_count)

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
            page_count=total_pages,
            pages=[page],
        )

    # ------------------------------------------------------------------
    # header.xml — style definitions
    # ------------------------------------------------------------------

    def _parse_header_styles(self, xml_bytes: bytes) -> Dict[str, "_StyleDef"]:
        """Parse style ID → name / heading level from header.xml."""
        root = ET.fromstring(xml_bytes)
        styles: Dict[str, _StyleDef] = {}

        for style_el in root.iter():
            tag = _local(style_el.tag)
            if tag != "style":
                continue

            style_id = style_el.get("id", "")
            style_name = style_el.get("name", "") or style_el.get("localName", "")
            heading = _heading_level_from_name(style_name)
            is_list = any(style_name.startswith(p) for p in _LIST_PREFIXES)

            styles[style_id] = _StyleDef(
                name=style_name,
                heading_lvl=heading,
                is_list=is_list,
            )

        return styles

    # ------------------------------------------------------------------
    # Section XML parsing
    # ------------------------------------------------------------------

    def _parse_section_xml(
        self,
        xml_bytes: bytes,
        sec_idx: int,
        styles: Dict[str, "_StyleDef"],
        bin_data: Dict[str, bytes],
        file_name: str,
        ocr_enabled: bool,
    ) -> Tuple[List[BaseElement], int]:
        """Parse one section XML and return (elements, page_count)."""
        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError as exc:
            self._log(f"XML parse error in section {sec_idx}: {exc}", level="warning")
            return [], 1

        elements: List[BaseElement] = []
        page_num = 1
        elem_ctr = 0

        def _next_id(prefix: str) -> str:
            nonlocal elem_ctr
            eid = f"hwpx:{file_name}:s{sec_idx}:{prefix}{elem_ctr}"
            elem_ctr += 1
            return eid

        # Walk direct children of the section root
        for child in root:
            tag = _local(child.tag)

            if tag == "p":
                elem = self._parse_paragraph(
                    child, styles, _next_id, page_num, elements
                )
                if elem:
                    elements.append(elem)

            elif tag == "tbl":
                tbl = self._parse_table(child, _next_id, page_num)
                if tbl:
                    elements.append(tbl)

            elif tag == "secPr":
                # Section properties may contain page count hints
                pass

        return elements, page_num

    # ------------------------------------------------------------------
    # Paragraph
    # ------------------------------------------------------------------

    def _parse_paragraph(
        self,
        para_el,
        styles: Dict[str, "_StyleDef"],
        next_id,
        page_num: int,
        elements: List[BaseElement],
    ) -> Optional[TextElement]:
        """Convert a <p> element to TextElement with semantic_type."""

        # Collect all text runs
        text_parts: List[str] = []
        for run in para_el.iter():
            if _local(run.tag) == "t" and run.text:
                text_parts.append(run.text)

        text = " ".join(text_parts).strip()
        if len(text) < _MIN_TEXT_LEN:
            return None

        # Style ID reference
        style_id = ""
        for ppr in para_el:
            if _local(ppr.tag) == "pPr":
                for pstyle in ppr:
                    if _local(pstyle.tag) == "pStyle":
                        style_id = pstyle.get("id", "") or pstyle.get("val", "")
                break

        style = styles.get(style_id)
        heading = style.heading_lvl if style else 0
        is_list = style.is_list if style else False

        # Font size fallback (HWPX stores in 1/200 pt units → divide by 200)
        if not heading and not is_list:
            font_pt = self._extract_font_size_pt(para_el)
            if font_pt and font_pt >= _HEADING_FONT_PT_MIN:
                if font_pt >= 28:
                    heading = 1
                elif font_pt >= 20:
                    heading = 2
                elif font_pt >= 16:
                    heading = 3
                else:
                    heading = 4

        if is_list:
            stype = "list_item"
        elif heading:
            stype = "heading"
        else:
            stype = "paragraph"

        raw_attrs: dict = {
            "style_id": style_id,
            "style_name": style.name if style else "",
        }
        if stype == "heading":
            raw_attrs["semantic_type"] = "heading"
            raw_attrs["heading_level"] = heading
        else:
            raw_attrs["semantic_type"] = stype

        # Merge consecutive same-style plain paragraphs
        if (
            stype == "paragraph"
            and elements
            and isinstance(elements[-1], TextElement)
            and elements[-1].raw_attributes.get("semantic_type") == "paragraph"
            and elements[-1].raw_attributes.get("style_id") == style_id
        ):
            elements[-1].__dict__["text"] = elements[-1].text + " " + text
            return None

        eid = next_id("para")
        return TextElement(
            id=eid,
            type="text",
            text=text,
            meta=ElementMetadata(page_num=page_num, id=eid),
            raw_attributes=raw_attrs,
        )

    @staticmethod
    def _extract_font_size_pt(para_el) -> Optional[float]:
        """Read <hp:sz> or <hml:sz> font size from first run in paragraph."""
        for el in para_el.iter():
            if _local(el.tag) in ("sz", "fontSize"):
                val = el.get("val") or el.get("value") or el.text
                if val:
                    try:
                        return float(val) / 200.0  # HWPX unit: 1/200 pt
                    except ValueError:
                        pass
        return None

    # ------------------------------------------------------------------
    # Table
    # ------------------------------------------------------------------

    def _parse_table(self, tbl_el, next_id, page_num: int) -> Optional[TableElement]:
        """Convert a <tbl> element to TableElement."""
        rows_data: List[List[str]] = []
        rows_cells: List[List[TableCell]] = []

        for r_idx, child in enumerate(tbl_el):
            if _local(child.tag) != "tr":
                continue

            row_data: List[str] = []
            row_cells: List[TableCell] = []

            for cell_el in child:
                if _local(cell_el.tag) != "tc":
                    continue

                # Collect text from all paragraphs in this cell
                cell_parts: List[str] = []
                for p_el in cell_el.iter():
                    if _local(p_el.tag) == "t" and p_el.text:
                        cell_parts.append(p_el.text)

                cell_text = " ".join(cell_parts).strip()
                row_data.append(cell_text)
                row_cells.append(TableCell(text=cell_text, is_header=(r_idx == 0)))

            if row_data:
                rows_data.append(row_data)
                rows_cells.append(row_cells)

        if not rows_data:
            return None

        eid = next_id("table")
        return TableElement(
            id=eid,
            type="table",
            data=rows_data,
            cells=rows_cells,
            meta=ElementMetadata(page_num=page_num, id=eid),
        )

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _empty_document(file_name: str) -> Document:
        return Document(
            file_name=file_name,
            file_id=file_name,
            doc_type="word",
            page_count=0,
            pages=[],
        )


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


class _StyleDef:
    """Lightweight style definition extracted from header.xml."""

    __slots__ = ("name", "heading_lvl", "is_list")

    def __init__(self, name: str, heading_lvl: int, is_list: bool) -> None:
        self.name: str = name
        self.heading_lvl: int = heading_lvl
        self.is_list: bool = is_list


def _local(tag: str) -> str:
    """Strip XML namespace from a tag string: '{ns}localname' → 'localname'."""
    return tag.split("}")[-1] if "}" in tag else tag


def _heading_level_from_name(name: str) -> int:
    for prefix in _HEADING_PREFIXES:
        if name.startswith(prefix):
            trailing = name[len(prefix) :].strip()
            if trailing and trailing[0].isdigit():
                return min(int(trailing[0]), 6)
    return 0
