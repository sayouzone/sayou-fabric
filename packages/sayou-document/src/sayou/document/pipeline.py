import os
from typing import Dict, List, Optional

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import safe_run

from .interfaces.base_parser import BaseDocumentParser
from .interfaces.base_ocr import BaseOCR
from .interfaces.base_converter import BaseConverter
from .models import Document
from .core.exceptions import ParserError

from .parser.docx_parser import DocxParser
from .parser.excel_parser import ExcelParser
from .parser.pdf_parser import PdfParser
from .parser.pptx_parser import PptxParser

from .converter.image_converter import ImageToPdfConverter
from .ocr.tesseract_ocr import TesseractOCR


class DocumentPipeline(BaseComponent):
    """
    Orchestrates the document parsing process.

    Features:
    - Automatic Parser selection based on file extension.
    - Smart Image Handling: Converts Images -> PDF -> Parsed via PdfParser(OCR).
    - OCR Injection for scanned documents.
    """

    component_name = "DocumentPipeline"

    def __init__(
        self,
        ocr_engine: Optional[BaseOCR] = None,
        extra_parsers: Optional[List[BaseDocumentParser]] = None,
        use_default_ocr: bool = False,
    ):
        super().__init__()

        self.ocr_engine = ocr_engine
        if not self.ocr_engine and use_default_ocr:
            if TesseractOCR:
                try:
                    self.ocr_engine = TesseractOCR()
                    self._log("Default TesseractOCR engine loaded.")
                except Exception as e:
                    self._log(
                        f"Failed to initialize TesseractOCR: {e}", level="warning"
                    )
            else:
                self._log(
                    "TesseractOCR requested but 'pytesseract' not installed.",
                    level="warning",
                )

        self.handler_map: Dict[str, BaseDocumentParser] = {}
        self.image_converter: BaseConverter = ImageToPdfConverter()

        default_parsers = [
            PdfParser(ocr_engine=self.ocr_engine),
            DocxParser(),
            PptxParser(),
            ExcelParser(),
        ]

        if self.ocr_engine:
            for p in default_parsers:
                p.set_ocr_engine(self.ocr_engine)

        self._register(default_parsers)

        if extra_parsers:
            self._register(extra_parsers)

    def _register(self, parsers: List[BaseDocumentParser]):
        for parser in parsers:
            for ext in getattr(parser, "SUPPORTED_TYPES", []):
                self.handler_map[ext.lower()] = parser

    @safe_run(default_return=None)
    def initialize(self, **kwargs):
        """
        Initialize all registered parsers, converter, and the OCR engine.
        """
        if self.ocr_engine:
            self.ocr_engine.initialize(**kwargs)

        self.image_converter.initialize(**kwargs)

        for parser in set(self.handler_map.values()):
            parser.initialize(**kwargs)

        self._log(f"DocumentPipeline initialized. Handlers: {len(self.handler_map)}")

    def run(self, file_bytes: bytes, file_name: str) -> Optional[Document]:
        """
        Parse a document file.

        [Smart Routing]
        If the input is an image (jpg, png, etc.), it is converted to PDF first,
        and then processed by the PdfParser to leverage its OCR capabilities.

        Args:
            file_bytes (bytes): File content.
            file_name (str): Filename with extension.

        Returns:
            Document: Parsed document object.
        """
        if not file_bytes:
            raise ParserError("Input file bytes are empty.")

        ext = os.path.splitext(file_name)[1].lower()

        if ext in self.image_converter.SUPPORTED_TYPES:
            self._log(f"Image detected ({ext}). Converting to PDF for processing...")
            try:
                pdf_bytes = self.image_converter.convert(file_bytes, file_name)
                if pdf_bytes:
                    file_bytes = pdf_bytes
                    ext = ".pdf"
                    self._log(
                        "Image converted to PDF successfully. Proceeding to OCR..."
                    )
            except Exception as e:
                self._log(f"Image conversion failed: {e}", level="error")
                raise ParserError(f"Failed to convert image {file_name}: {e}")

        handler = self.handler_map.get(ext)

        if not handler:
            supported = (
                list(self.handler_map.keys()) + self.image_converter.SUPPORTED_TYPES
            )
            raise ParserError(
                f"No parser found for extension '{ext}'. Supported: {supported}"
            )

        self._log(f"Routing '{file_name}' to {handler.component_name}...")

        return handler.parse(file_bytes, file_name)
