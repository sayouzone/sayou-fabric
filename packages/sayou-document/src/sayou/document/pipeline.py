import os
from typing import List, Dict, Optional

from sayou.core.base_component import BaseComponent

from .interfaces.base_parser import BaseDocumentParser, BaseOCR
from .models import Document
from .parsers.pdf_parser import PdfParser
from .parsers.docx_parser import DocxParser
from .parsers.pptx_parser import PptxParser
from .parsers.excel_parser import ExcelParser

class DocumentPipeline(BaseComponent):
    component_name = "DocumentPipeline"

    def __init__(
        self, 
        ocr_engine: Optional[BaseOCR] = None,
        extra_parsers: Optional[List[BaseDocumentParser]] = None
    ):
        self.ocr_engine = ocr_engine
        self.handler_map: Dict[str, BaseDocumentParser] = {}

        default_parsers = [
            PdfParser(ocr_engine=self.ocr_engine),
            DocxParser(),
            PptxParser(),
            ExcelParser()
        ]

        self._register(default_parsers)
        if extra_parsers:
            self._register(extra_parsers)

    def _register(self, parsers: List[BaseDocumentParser]):
        for parser in parsers:
            for ext in getattr(parser, "SUPPORTED_TYPES", []):
                self.handler_map[ext.lower()] = parser

    def initialize(self, **kwargs):
        for parser in set(self.handler_map.values()):
            parser.initialize(**kwargs)
        self._log(f"Initialized covering {len(self.handler_map)} extensions.")

    def run(self, file_bytes: bytes, file_name: str) -> Document:
        ext = os.path.splitext(file_name)[1].lower()
        handler = self.handler_map.get(ext)
        
        if not handler:
            raise ValueError(f"No parser found for extension: {ext}")
            
        self._log(f"Routing '{file_name}' to {handler.component_name}...")
        return handler.parse(file_bytes, file_name)