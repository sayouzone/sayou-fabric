from abc import abstractmethod
from typing import List, Optional
from sayou.core.base_component import BaseComponent
from sayou.document.models import Document, ImageElement, ElementMetadata, BoundingBox
from .base_ocr import BaseOCR 

class BaseDocumentParser(BaseComponent):
    """
    (Tier 1) 모든 문서 파서의 부모 클래스입니다.
    공통적인 로깅, 에러 처리, OCR 엔진 주입 기능을 제공합니다.
    """
    component_name = "BaseDocumentParser"
    SUPPORTED_TYPES: List[str] = []

    def __init__(self):
        super().__init__()
        self.ocr_engine: Optional[BaseOCR] = None

    def set_ocr_engine(self, ocr_engine: Optional[BaseOCR]):
        """(선택적) 스캔본 처리를 위한 OCR 엔진을 주입합니다."""
        self.ocr_engine = ocr_engine
        if ocr_engine:
            self._log(f"OCR Engine '{ocr_engine.component_name}' attached.")

    def parse(self, file_bytes: bytes, file_name: str, **kwargs) -> Document:
        """
        [공통 뼈대] 파싱 프로세스의 템플릿 메서드입니다.
        1. 입력 검증
        2. 실제 파싱 (_parse 호출)
        3. 결과 로깅 및 반환
        """
        self._log(f"Parsing file: {file_name} ({len(file_bytes)} bytes)")
        
        if not file_bytes:
            self._log("[WARNING] Received empty file bytes.")
            return None

        try:
            document = self._parse(file_bytes, file_name, **kwargs)
            if document:
                self._log(f"Successfully extracted  pages from {file_name}.")
            else:
                self._log("[WARNING] Parser returned None.")

            return document

        except Exception as e:
            self._log(f"[ERROR] Failed to parse {file_name}: {e}")
            raise e 

    @abstractmethod
    def _parse(self, file_bytes: bytes, file_name: str, **kwargs) -> Document:
        """
        [구현 필수] 실제 파싱 로직 (Tier 2에서 구현)
        반환 타입이 List[DataAtom] -> Document 로 변경되었습니다.
        """
        raise NotImplementedError

    def _process_image_data(self, image_bytes: bytes, img_format: str, 
                            elem_id: str, page_num: int, 
                            bbox: Optional[BoundingBox] = None, 
                            ocr_enabled: bool = True) -> ImageElement:
        """
        [공통 방어선] 모든 파서가 이미지를 발견하면 이 메서드를 호출합니다.
        OCR 엔진이 있고 ocr_enabled가 True면, 자동으로 OCR을 수행합니다.
        """
        import base64
        
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        ocr_text = None

        if ocr_enabled and self.ocr_engine:
            try:
                extracted = self.ocr_engine.ocr_bytes(image_bytes)
                if extracted and extracted.strip():
                    ocr_text = extracted.strip()
                    self._log(f"OCR extracted {len(ocr_text)} chars from image {elem_id}")
            except Exception as e:
                self._log(f"OCR failed for image {elem_id}: {e}", level="warning")

        return ImageElement(
            id=elem_id,
            type="image",
            bbox=bbox,
            meta=ElementMetadata(page_num=page_num, id=elem_id),
            image_base64=image_base64,
            image_format=img_format,
            ocr_text=ocr_text
        )