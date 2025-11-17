# Library Guide: sayou-document

`sayou-document` is the **high-fidelity document extraction library** that powers the first step of the `sayou-rag` pipeline.

The library's core philosophy is **"Precise Extraction."** It focuses on capturing the structural facts of a document—such as fonts, styles, coordinates, and layout—and structuring them **without loss of fidelity**. This rich, reliable data provides a robust foundation for intelligent, rule-based processing by downstream components like `sayou-refinery`.

Within `sayou-rag`, this library serves as the default plugin for the 'Extractor' slot in the `AdvancedRAG` pipeline. It can also be used as a powerful standalone library.

---

## 1. Independent Installation

To use `sayou-document` independently of the main `sayou-rag` package, you can install it directly:

```bash
pip install sayou-document
```

## 2. Core Concepts & Architecture

`sayou-document` is built on a 3-Tier architecture, ensuring high extensibility.

### Tier 1: Interfaces (The Contract)

Abstract base classes that define the component contracts.

* `BaseDocumentParser`: Defines the `.parse()` method.
* `BaseOCR`: Defines the `.ocr_bytes()` method.
* `BaseConverter`: Defines the `.convert()` method.

### Tier 2: Templates (The Defaults)

The default, "batteries-included" implementations of the interfaces.

* `PdfParser`: Based on `fitz(PyMuPDF)`. Supports TOC, scanned PDF detection, and image OCR.
* `DocxParser`: Based on `python-docx`. Supports headers, footers, and style extraction.
* `PptxParser`: Based on `python-pptx`. Supports charts, slide notes, and `placeholder_type` extraction.
* `ExcelParser`: Based on `openpyxl`. Supports hidden sheets, sheet names, and image extraction.

### Tier 3: Plugins (The Customization)

Any user-implemented component that adheres to a Tier 1 interface. (e.g., `GoogleVisionOCR`, `HwpConverter`)

---

## 3. Usage Examples

### Basic Usage (Independent)

The `DocumentPipeline` automatically loads Tier 2 parsers and routes files by extension.

```python
import os
from sayou.document.pipeline import DocumentPipeline

# 1. Initialize the pipeline (Defaults are loaded)
pipeline = DocumentPipeline()
pipeline.initialize()

# 2. Load file bytes
file_path = "path/to/your/financial_report.pdf"
file_name = os.path.basename(file_path)

with open(file_path, "rb") as f:
    file_bytes = f.read()

# 3. Run extraction
doc = pipeline.run(file_bytes, file_name)

# 4. Export to JSON
json_output = doc.model_dump_json(indent=2)
print(json_output)
```

### Advanced Usage (Injecting Plugins)

The true power of `sayou-document` lies in dependency injection. You can provide Tier 3 plugins to the `DocumentPipeline` constructor to extend or replace default behaviors.

```python
from sayou.document.pipeline import DocumentPipeline

from my_plugins.ocr import MyCustomTesseractOCR
from my_plugins.converters import MyHwpConverter

my_ocr = MyCustomTesseractOCR(tesseract_path="/usr/bin/tesseract")

my_converter = MyHwpConverter(libreoffice_path="/usr/bin/soffice")

pipeline = DocumentPipeline(
    ocr_engine=my_ocr,
    converter=my_converter
)
pipeline.initialize()

hwp_doc = pipeline.run(hwp_file_bytes, "report.hwp")
```

---

## 4. The `Document` Output Schema

All parsers return a single, consistent Pydantic model.

### 4.1. Root (`Document`)

The top-level container for the entire document.

```json
{
  "file_name": "string",
  "file_id": "string",
  "doc_type": "Literal['pdf', 'word', 'slide', 'sheet', 'unknown']",
  "metadata": {
    "title": "Optional[string]",
    "author": "Optional[string]",
    // ...
  },
  "page_count": "int",
  "pages": "List[Union[Page, Slide, Sheet]]",
  "toc": "List[Dict]"
}
```

### 4.2. Containers (`Page`, `Slide`, `Sheet`)

The `pages` list holds containers specific to the document type.

* **`Page`** (PDF, Word):
    * `page_num: int`
    * `width: float`, `height: float`
    * `elements: List[ElementUnion]`
    * `header_elements: List[ElementUnion]` (Word)
    * `footer_elements: List[ElementUnion]` (Word)
    * `text: string` (Page text dump)
* **`Slide`** (PPTX):
    * `page_num: int`
    * `elements: List[ElementUnion]`
    * `note_text: Optional[string]` (Slide notes)
* **`Sheet`** (XLSX):
    * `page_num: int` (Sheet index)
    * `sheet_name: string`
    * `is_hidden: bool`
    * `elements: List[ElementUnion]` (Usually one `TableElement`)

### 4.3. Elements (The Content)

`ElementUnion = Union[TextElement, TableElement, ImageElement, ChartElement]`

All elements inherit from `BaseElement` and share:

* `id: string` (e.g., "p1:b3")
* `type: string` ("text", "table", "image", "chart")
* `bbox: BoundingBox` (Coordinates)
* `meta: ElementMetadata` (`page_num`, etc.)
* **`raw_attributes: Dict`**: **(High-Fidelity Core)** A "catch-all" pocket for all other original properties extracted by the parser (e.g., `{"style": "Heading 1"}`, `{"placeholder_type": "TITLE"}`).

---

* **`TextElement`**:
    * `text: string`
    * `style: Optional[TextStyle]` (Font name, size, bold, etc.)
* **`TableElement`**:
    * `data: List[List[string]]` (A 2D list for LLM-friendly processing)
    * `cells: List[List[TableCell]]` (For structural data, like merged cells. v0.1.0+)
* **`ImageElement`**:
    * `image_base64: string`
    * `ocr_text: Optional[string]` (Result from the OCR engine)
* **`ChartElement`** (PPTX):
    * `chart_title: string`
    * `chart_type: string`
    * `text_representation: string` (LLM-friendly text conversion)
    * `raw_attributes`: (Preserves original `chart.series` data)

---

## 5. Tier 2 Default Parsers Deep Dive

High-fidelity details provided by the default parsers.

* **`PdfParser`**:
    * Populates `Document.toc` from `fitz.get_toc()`.
    * Automatically detects scanned (image-only) PDFs to perform full-page OCR.
    * Supports OCR for embedded image blocks (`b_type == 1`).
* **`DocxParser`**:
    * Populates `Page.header_elements` and `Page.footer_elements`.
    * Populates `TextElement.raw_attributes["style"]` with Word style names (e.g., "Heading 1").
* **`PptxParser`**:
    * Populates `Element.raw_attributes["placeholder_type"]` (e.g., "TITLE", "BODY") for semantic layout analysis.
    * Extracts `ChartElement` data and `Slide.note_text` (speaker notes).
* **`ExcelParser`**:
    * Populates `Sheet.is_hidden` and `Sheet.sheet_name`.
    * Extracts `XLImage` (images embedded in sheets) and supports OCR.
    * *Roadmap (v0.1.0)*: `TableCell.style` (cell formatting, merge info).

---

## 6. Extending (Tier 3 Guide)

The most common extensions are custom OCR engines or file converters.

### Example: Creating a Custom OCR Plugin

```python
from sayou.document.interfaces.base_ocr import BaseOCR
import my_ocr_library # (가상의 라이브러리)

class MyAwesomeOCR(BaseOCR):
    """(Tier 3) MyAwesomeOCR의 인터페이스 구현체"""
    
    component_name = "MyAwesomeOCR"

    def __init__(self, api_key: str):
        super().__init__()
        self.client = my_ocr_library.Client(api_key=api_key)
        self._log(f"MyAwesomeOCR initialized.")

    @abstractmethod
    def _do_ocr(self, image_bytes: bytes, **kwargs) -> str:
        """
        [구현 필수] BaseOCR의 추상 메서드 구현.
        실제 OCR 로직은 여기서 처리합니다.
        """
        try:
            # BaseOCR.ocr_bytes()가 에러 핸들링을 해주므로,
            # 여기서는 성공 시 텍스트 반환에만 집중합니다.
            results = self.client.process(image=image_bytes)
            return results.text
        except Exception as e:
            self._log(f"MyAwesomeOCR failed: {e}", level="error")
            return "" # 실패 시 빈 문자열 반환
```

```python
from sayou.document.pipeline import DocumentPipeline

ocr_plugin = MyAwesomeOCR(api_key="MY_SECRET_KEY")
pipeline = DocumentPipeline(ocr_engine=ocr_plugin)

pipeline.run(...)
```