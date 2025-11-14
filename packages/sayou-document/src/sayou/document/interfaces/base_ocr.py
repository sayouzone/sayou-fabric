from abc import abstractmethod
from typing import Any
from sayou.core.base_component import BaseComponent

class BaseOCR(BaseComponent):
    """
    (Tier 1) OCR 엔진 인터페이스.
    """
    component_name = "BaseOCR"

    def ocr_bytes(self, image_bytes: bytes, **kwargs) -> str:
        """
        [공통 뼈대] OCR 실행 전처리/후처리
        """
        if not image_bytes:
            return ""
            
        try:
            text = self._do_ocr(image_bytes, **kwargs)
            return text.strip()
        except Exception as e:
            self._log(f"OCR failed: {e}", level="error")
            return ""

    @abstractmethod
    def _do_ocr(self, image_bytes: bytes, **kwargs) -> str:
        """[구현 필수] 실제 OCR 로직 (e.g., Google Vision 호출)"""
        raise NotImplementedError