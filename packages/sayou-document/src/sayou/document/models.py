from typing import List, Optional, Union, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict

# ==============================================================================
# 1. Atom (최소 단위) - Common Schema 기반
# ==============================================================================

class BoundingBox(BaseModel):
    """(x0, y0, x1, y1) Normalized coordinates"""
    x0: float = 0.0
    y0: float = 0.0
    x1: float = 0.0
    y1: float = 0.0

class TextStyle(BaseModel):
    """High-Fidelity Font/Style Information"""
    font_name: Optional[str] = None
    font_size: Optional[float] = None
    color: Optional[str] = None
    is_bold: bool = False
    is_italic: bool = False
    is_underlined: bool = False

class ElementMetadata(BaseModel):
    """모든 요소가 공통으로 가지는 메타데이터."""
    model_config = ConfigDict(extra='allow') # 정의되지 않은 필드도 허용
    
    page_num: int
    id: Optional[str] = None
    link: Optional[str] = None

# ==============================================================================
# 2. Elements (콘텐츠 요소) - 모든 문서 공통
# ==============================================================================

class BaseElement(BaseModel):
    """
    The building block of any document.
    Equivalent to 'contents' items in the original schema.
    """
    id: str
    type: str
    bbox: Optional[BoundingBox] = None
    
    # 원본 스키마의 자잘한 속성들(z-order, rotation 등) 보존
    raw_attributes: Dict[str, Any] = {}
    model_config = ConfigDict(extra='allow')

class TextElement(BaseElement):
    type: Literal["text"] = "text"
    text: str
    style: Optional[TextStyle] = None
    meta: ElementMetadata

class TableCell(BaseModel):
    """Atomic unit of a table"""
    text: str
    row_span: int = 1
    col_span: int = 1
    is_header: bool = False
    bbox: Optional[BoundingBox] = None

class TableElement(BaseElement):
    type: Literal["table"] = "table"
    data: List[List[str]]
    cells: List[List[TableCell]] = []
    caption: Optional[str] = None
    meta: ElementMetadata

class ImageElement(BaseElement):
    type: Literal["image"] = "image"
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    caption: Optional[str] = None
    ocr_text: Optional[str] = None
    meta: ElementMetadata

class ChartElement(BaseElement):
    type: Literal["chart"] = "chart"
    chart_title: Optional[str] = None
    chart_type: Optional[str] = None
    text_representation: Optional[str] = None
    meta: ElementMetadata

# ==============================================================================
# 3. Containers (그릇) - 각 스키마 특화 영역
# ==============================================================================

class BasePage(BaseModel):
    """Abstract container for content"""
    page_num: int
    width: Optional[float] = None
    height: Optional[float] = None
    elements: List[Union[TextElement, TableElement, ImageElement, ChartElement]] = []

class Page(BasePage):
    """For PDF and Word (Sequential Pages)"""
    header_elements: List[Union[TextElement, TableElement, ImageElement, ChartElement]] = []
    footer_elements: List[Union[TextElement, TableElement, ImageElement, ChartElement]] = []
    text: Optional[str] = None

class Slide(BasePage):
    """For PPT (Presentation Slides)"""
    has_notes: bool = False
    note_text: Optional[str] = None
    master_slide_id: Optional[str] = None

class Sheet(BasePage):
    """For Excel (Spreadsheet Tabs)"""
    sheet_name: str
    is_hidden: bool = False
    sheet_index: int

# ==============================================================================
# 4. The Document (Root) - 통합 인터페이스
# ==============================================================================

class Page(BaseModel):
    page_num: int
    width: Optional[float] = None
    height: Optional[float] = None
    elements: List[Union[TextElement, TableElement, ImageElement]] = []
    text: Optional[str] = None

class DocumentMetadata(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    source_path: Optional[str] = None
    extra: Dict[str, Any] = {}

class Document(BaseModel):
    """
    The Final Artifact.
    This structure can hold ANY of the 4 document types 
    while preserving their unique structures.
    """
    file_name: str
    file_id: str
    doc_type: Literal["pdf", "word", "slide", "sheet", "unknown"]
    
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    page_count: int = 0

    pages: List[Union[Page, Slide, Sheet]] = []
    
    toc: List[Dict[str, Any]] = [] # Bookmarks/Table of Contents
    links: List[Dict[str, Any]] = [] # Global Hyperlinks