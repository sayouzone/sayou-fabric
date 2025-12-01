try:
    import io

    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None

from ..core.exceptions import OCRError
from ..interfaces.base_ocr import BaseOCR


class TesseractOCR(BaseOCR):
    """
    (Tier 2) OCR implementation using Google's Tesseract engine via 'pytesseract'.
    """

    component_name = "TesseractOCR"

    def initialize(self, lang: str = "eng+kor", **kwargs):
        """
        Args:
            lang (str): Language code string (e.g., 'eng', 'kor', 'eng+kor').
        """
        self.lang = lang

    def _do_ocr(self, image_bytes: bytes, **kwargs) -> str:
        if not pytesseract:
            raise ImportError("pytesseract and Pillow are required for TesseractOCR.")

        try:
            image = Image.open(io.BytesIO(image_bytes))
            # pytesseract는 이미지가 메모리에 있으면 바로 처리 가능
            text = pytesseract.image_to_string(image, lang=self.lang)
            return text
        except Exception as e:
            # Tesseract 바이너리가 없거나 경로 문제일 수 있음
            raise OCRError(f"Tesseract execution failed: {e}")
