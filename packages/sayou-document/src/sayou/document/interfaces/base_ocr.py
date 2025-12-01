from abc import abstractmethod

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time


class BaseOCR(BaseComponent):
    """
    (Tier 1) Abstract base class for OCR engines.
    """

    component_name = "BaseOCR"

    @measure_time
    def ocr_bytes(self, image_bytes: bytes, **kwargs) -> str:
        """
        Execute OCR on image bytes.

        Args:
            image_bytes (bytes): Image content.

        Returns:
            str: Extracted text.
        """
        if not image_bytes:
            return ""

        try:
            text = self._do_ocr(image_bytes, **kwargs)
            return text.strip()
        except Exception as e:
            self._log(f"OCR execution failed: {e}", level="warning")
            return ""

    @abstractmethod
    def _do_ocr(self, image_bytes: bytes, **kwargs) -> str:
        """
        [Abstract Hook] Implement the actual OCR API call.
        """
        raise NotImplementedError
