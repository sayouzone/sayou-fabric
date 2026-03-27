"""
Unit tests for ImageToPdfConverter.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sayou.document.converter.image_converter import ImageToPdfConverter


JPEG_MAGIC = b"\xff\xd8\xff\xe0" + b"\x00" * 14
PNG_MAGIC = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
BMP_MAGIC = b"BM" + b"\x00" * 6
TIFF_LE = b"II*\x00" + b"\x00" * 4


class TestImageToPdfConverterCanHandle:
    def test_jpeg_magic(self):
        assert ImageToPdfConverter.can_handle(JPEG_MAGIC, "photo.jpg") == 1.0

    def test_png_magic(self):
        assert ImageToPdfConverter.can_handle(PNG_MAGIC, "image.png") == 1.0

    def test_bmp_magic(self):
        assert ImageToPdfConverter.can_handle(BMP_MAGIC, "img.bmp") == 1.0

    def test_tiff_le(self):
        assert ImageToPdfConverter.can_handle(TIFF_LE, "scan.tiff") == 1.0

    def test_extension_fallback_jpg(self):
        assert ImageToPdfConverter.can_handle(b"\x00\x00", "photo.jpg") == 0.8

    def test_non_image_returns_0(self):
        assert ImageToPdfConverter.can_handle(b"%PDF", "doc.pdf") == 0.0


class TestImageToPdfConverterConvert:
    @patch("sayou.document.converter.image_converter.Image")
    def test_returns_pdf_bytes(self, MockImage):
        """The converter should return bytes that start with %PDF."""
        import io

        # Simulate Image.open + save producing PDF bytes
        mock_img = MagicMock()
        mock_img.mode = "RGB"
        MockImage.open.return_value = mock_img

        def fake_save(buf, format, **kwargs):
            buf.write(b"%PDF-1.4 fake pdf content")

        mock_img.save.side_effect = fake_save

        converter = ImageToPdfConverter()
        result = converter._do_convert(JPEG_MAGIC, "photo.jpg")
        assert result.startswith(b"%PDF")

    @patch("sayou.document.converter.image_converter.Image")
    def test_rgba_converted_to_rgb(self, MockImage):
        """RGBA images must be composited onto white before PDF save."""
        import io

        mock_img = MagicMock()
        mock_img.mode = "RGBA"
        mock_img.size = (100, 100)
        MockImage.open.return_value = mock_img

        # Background created via Image.new
        bg = MagicMock()
        bg.mode = "RGB"
        MockImage.new.return_value = bg

        def fake_save(buf, format, **kwargs):
            buf.write(b"%PDF-fake")

        bg.save.side_effect = fake_save

        converter = ImageToPdfConverter()
        result = converter._do_convert(PNG_MAGIC, "transparent.png")
        MockImage.new.assert_called_once_with("RGB", (100, 100), (255, 255, 255))
        assert result == b"%PDF-fake"
