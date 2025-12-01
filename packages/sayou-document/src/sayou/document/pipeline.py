import os
from typing import Dict, List, Optional

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import safe_run

from .core.exceptions import ParserError
from .interfaces.base_ocr import BaseOCR
from .interfaces.base_parser import BaseDocumentParser
from .models import Document
from .parsers.docx_parser import DocxParser
from .parsers.excel_parser import ExcelParser
from .parsers.pdf_parser import PdfParser
from .parsers.pptx_parser import PptxParser


class DocumentPipeline(BaseComponent):
    """
    Orchestrates the document parsing process.
    Routes input files to the appropriate parser based on extension.
    """

    component_name = "DocumentPipeline"

    def __init__(
        self,
        ocr_engine: Optional[BaseOCR] = None,
        extra_parsers: Optional[List[BaseDocumentParser]] = None,
    ):
        super().__init__()
        self.ocr_engine = ocr_engine
        self.handler_map: Dict[str, BaseDocumentParser] = {}

        default_parsers = [
            PdfParser(),
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
        Initialize all registered parsers.
        """
        for parser in set(self.handler_map.values()):
            parser.initialize(**kwargs)

        self._log(
            f"DocumentPipeline initialized. Supports: {list(self.handler_map.keys())}"
        )

    def run(self, file_bytes: bytes, file_name: str) -> Optional[Document]:
        """
        Parse a document file.

        Args:
            file_bytes (bytes): File content.
            file_name (str): Filename with extension.

        Returns:
            Document: Parsed document object.
        """
        ext = os.path.splitext(file_name)[1].lower()
        handler = self.handler_map.get(ext)

        if not handler:
            supported = list(self.handler_map.keys())
            raise ParserError(
                f"No parser found for extension '{ext}'. Supported: {supported}"
            )

        self._log(f"Routing '{file_name}' to {handler.component_name}...")

        return handler.parse(file_bytes, file_name)
