import unittest
from unittest.mock import MagicMock, patch

from sayou.document.models import Document
from sayou.document.pipeline import DocumentPipeline


class TestDocumentPipeline(unittest.TestCase):

    def setUp(self):
        # OCR 엔진 없이 파이프라인 초기화
        self.pipeline = DocumentPipeline(use_default_ocr=False)
        self.pipeline.initialize()

    def test_routing_pdf(self):
        """PDF 파일이 PdfParser로 라우팅되는지 확인"""
        dummy_pdf = b"%PDF-1.4..."

        # PdfParser의 parse 메서드를 Mocking
        mock_parser = MagicMock()
        mock_parser.component_name = "MockPdfParser"
        mock_parser.parse.return_value = Document(
            file_name="test.pdf", file_id="test", doc_type="pdf", page_count=1
        )

        # 파이프라인의 맵을 조작하여 Mock 파서 주입
        self.pipeline.handler_map[".pdf"] = mock_parser

        result = self.pipeline.run(dummy_pdf, "test.pdf")

        self.assertIsNotNone(result)
        self.assertEqual(result.doc_type, "pdf")
        mock_parser.parse.assert_called_once()

    @patch("sayou.document.pipeline.ImageToPdfConverter")
    def test_image_auto_conversion(self, MockConverter):
        """이미지 파일이 들어오면 변환 후 PDF 파서로 가는지 확인"""
        dummy_png = b"fake_png_bytes"
        converted_pdf = b"%PDF-converted"

        # 1. Converter Mock 설정
        mock_converter_instance = MockConverter.return_value
        mock_converter_instance.SUPPORTED_TYPES = [".png"]
        mock_converter_instance.convert.return_value = converted_pdf

        # 파이프라인의 converter를 Mock 객체로 교체
        self.pipeline.image_converter = mock_converter_instance

        # 2. PDF Parser Mock 설정
        mock_pdf_parser = MagicMock()
        mock_pdf_parser.parse.return_value = Document(
            file_name="image.png", file_id="img", doc_type="pdf", page_count=1
        )
        self.pipeline.handler_map[".pdf"] = mock_pdf_parser

        # 3. 실행 (.png 파일 투입)
        result = self.pipeline.run(dummy_png, "image.png")

        # 4. 검증
        # - Converter가 호출되었는지?
        mock_converter_instance.convert.assert_called_with(dummy_png, "image.png")
        # - PDF Parser가 '변환된 바이트'로 호출되었는지?
        mock_pdf_parser.parse.assert_called_with(converted_pdf, "image.png")
        # - 결과가 정상적으로 반환되었는지?
        self.assertIsNotNone(result)

    def test_unknown_extension(self):
        """지원하지 않는 확장자에 대한 에러 처리"""
        with self.assertRaises(Exception):  # ParserError
            self.pipeline.run(b"data", "unknown.xyz")


if __name__ == "__main__":
    unittest.main()
