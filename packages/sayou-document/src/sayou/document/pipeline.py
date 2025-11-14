import os
from typing import Dict, Optional, List, Type

from sayou.core.base_component import BaseComponent

from sayou.document.models import Document 

from sayou.document.interfaces.base_parser import BaseDocumentParser
from sayou.document.interfaces.base_converter import BaseConverter
from sayou.document.interfaces.base_ocr import BaseOCR

from sayou.document.parsers.pdf_parser import PdfParser
from sayou.document.parsers.docx_parser import DocxParser
from sayou.document.parsers.excel_parser import ExcelParser
from sayou.document.parsers.pptx_parser import PptxParser

class DocumentPipeline(BaseComponent):
    """
    (Orchestrator) 파일 확장자에 맞는 Parser를 선택하여 실행하는 지휘자.
    결과물로 Sayou 표준 규격인 'Document' Pydantic 객체를 반환합니다.
    """
    component_name = "DocumentPipeline"

    def __init__(
        self, 
        parsers: Optional[Dict[str, BaseDocumentParser]] = None,
        converter: Optional[BaseConverter] = None,
        ocr_engine: Optional[BaseOCR] = None
    ):
        """
        :param parsers: 확장자별 커스텀 파서 맵 (None이면 기본값 사용)
        :param converter: (선택) HWP 등을 처리할 변환기 플러그인
        :param ocr_engine: (선택) 스캔본을 처리할 OCR 플러그인
        """
        super().__init__()
        
        self.converter = converter
        self.ocr_engine = ocr_engine
        self.parser_map: Dict[str, BaseDocumentParser] = {}
        
        # 1. 파서 등록 (사용자 주입 or 기본값)
        if parsers:
            self.parser_map = parsers
        else:
            self._register_default_parsers()

        # 2. 모든 파서에게 OCR 엔진 주입 (USB 연결)
        if self.ocr_engine:
            for parser in self.parser_map.values():
                parser.set_ocr_engine(self.ocr_engine)

        self._log(f"Pipeline initialized with parsers: {list(self.parser_map.keys())}")

    def _register_default_parsers(self):
        """Tier 2 기본 파서들을 로드합니다."""
        defaults = [
            PdfParser(),
            DocxParser(),
            ExcelParser(),
            PptxParser()
        ]

        for parser in defaults:
            for ext in parser.SUPPORTED_TYPES:
                self.parser_map[ext.lower()] = parser

    def initialize(self, **kwargs):
        """하위 컴포넌트 초기화"""
        super().initialize(**kwargs)
        if self.ocr_engine:
            self.ocr_engine.initialize(**kwargs)
        if self.converter:
            self.converter.initialize(**kwargs)

    def run(self, file_bytes: bytes, file_name: str, **kwargs) -> Document:
        """
        파일을 받아 파싱하고 'Document' 객체를 반환합니다.
        """
        file_ext = os.path.splitext(file_name)[1].lower()
        self._log(f"Processing file: {file_name} ({file_ext})")

        # 1. 확장자에 맞는 파서 찾기
        parser = self.parser_map.get(file_ext)

        # 2. 파서 실행
        if parser:
            return parser.parse(file_bytes, file_name, **kwargs)
        
        # 3. 파서가 없다면? 변환기(Converter) 시도
        elif self.converter and file_ext in self.converter.SUPPORTED_TYPES:
            self._log(f"No parser for {file_ext}, attempting conversion...")
            
            # 변환 (e.g., HWP -> PDF bytes)
            converted_bytes = self.converter.convert(file_bytes, file_name)
            if not converted_bytes:
                raise ValueError(f"Conversion failed for {file_name}")

            # 변환된 파일(PDF)을 처리할 파서 재검색
            pdf_parser = self.parser_map.get(".pdf")
            if pdf_parser:
                # 가짜 파일명(.pdf)으로 파싱 수행
                return pdf_parser.parse(converted_bytes, file_name + ".pdf", **kwargs)
            else:
                raise ValueError("Converted to PDF, but no PDF parser is registered.")

        # 4. 지원하지 않는 파일
        else:
            supported = list(self.parser_map.keys())
            if self.converter:
                supported.extend(self.converter.SUPPORTED_TYPES)
            raise ValueError(f"Unsupported file type: {file_ext}. Supported: {supported}")