!!! abstract "Source"
    Synced from [`packages/sayou-document/examples/quick_start_image.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-document/examples/quick_start_image.py).

## Setup

Convert an image file (JPG, PNG, BMP, TIFF) to PDF and parse it, with
optional OCR for scanned text extraction.

`ImageToPdfConverter` uses Pillow to rasterize the image and wrap it in a
PDF envelope.  `DocumentPipeline` then passes the resulting PDF to
`PdfParser`.  If an OCR engine is supplied via the `ocr=` kwarg, the
full-page OCR path is triggered automatically when the page contains no
extractable text.

Install dependencies before running with a real file:

```bash
pip install pillow pymupdf pytesseract
python quick_start_image.py
```

```python
import json
from unittest.mock import MagicMock, patch

from sayou.document.pipeline import DocumentPipeline
from sayou.document.models import TextElement

OUTPUT_FILE = "image_result.json"
```

## Convert and Parse a Plain Image

Pass JPEG magic bytes (or real file content) as `file_bytes` with a `.jpg`
extension.  `DocumentPipeline` scores `ImageToPdfConverter` highest for
image files and routes through it before falling back to `PdfParser`.

No OCR is required for this path — text extraction uses PyMuPDF directly
on the converted PDF.

```python
JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 14  # minimal JPEG header


def _make_pdf_page(text=""):
    page = MagicMock()
    page.rect.width = 612.0
    page.rect.height = 792.0
    page.get_text.side_effect = lambda *a, **k: (
        {
            "blocks": [
                {
                    "type": 0,
                    "number": 0,
                    "bbox": (72, 72, 540, 90),
                    "lines": [{"spans": [{"text": text}]}],
                }
            ]
        }
        if text and a and a[0] == "dict"
        else ({} if a and a[0] == "dict" else text)
    )
    return page


with patch("sayou.document.converter.image_converter.Image") as MockImg, patch(
    "sayou.document.parser.pdf_parser.fitz"
) as mock_fitz:

    # Converter: Image.open → save → PDF bytes
    mock_img = MagicMock()
    mock_img.mode = "RGB"
    MockImg.open.return_value = mock_img
    mock_img.save.side_effect = lambda buf, fmt, **k: buf.write(b"%PDF-converted")

    # Parser: fitz reads the converted PDF
    mock_fitz.TEXTFLAGS_DICT = 0
    fdoc = MagicMock()
    fdoc.page_count = 1
    fdoc.load_page.return_value = _make_pdf_page()
    fdoc.get_toc.return_value = []
    mock_fitz.open.return_value = fdoc

    doc = DocumentPipeline.process(JPEG_BYTES, "scan.jpg")

print("=== Convert and Parse a Plain Image ===")
print(f"  doc_type   : {doc.doc_type}")
print(f"  page_count : {doc.page_count}")
```

## Scanned Image with OCR

When the converted PDF page yields no text (i.e. it is a pure scan),
`PdfParser` detects the empty page and hands the rendered bitmap to the
OCR engine.

Pass `ocr={"lang": "eng+kor"}` to enable OCR.  Optionally specify
`"engine_path"` if Tesseract is not on your PATH:

```python
ocr={"lang": "kor", "engine_path": "/usr/bin/tesseract"}
```

`TesseractOCR` uses `pytesseract` under the hood.  The extracted text is
stored in a `TextElement` with `id="p1:full_ocr"`.

```python
with patch("sayou.document.converter.image_converter.Image") as MockImg, patch(
    "sayou.document.parser.pdf_parser.fitz"
) as mock_fitz, patch(
    "sayou.document.ocr.tesseract_ocr.pytesseract"
) as mock_tess, patch(
    "sayou.document.ocr.tesseract_ocr.Image"
) as MockPilImg:

    # Converter stub
    mock_img = MagicMock()
    mock_img.mode = "RGB"
    MockImg.open.return_value = mock_img
    mock_img.save.side_effect = lambda buf, fmt, **k: buf.write(b"%PDF-converted")

    # Parser: page with no extractable text → triggers OCR
    empty_page = MagicMock()
    empty_page.rect.width = 612.0
    empty_page.rect.height = 792.0
    empty_page.get_text.return_value = ""
    pix = MagicMock()
    pix.tobytes.return_value = b"fake_png"
    empty_page.get_pixmap.return_value = pix

    fdoc2 = MagicMock()
    fdoc2.page_count = 1
    fdoc2.load_page.return_value = empty_page
    fdoc2.get_toc.return_value = []
    mock_fitz.TEXTFLAGS_DICT = 0
    mock_fitz.open.return_value = fdoc2

    # OCR stub
    mock_tess.image_to_string.return_value = (
        "안녕하세요 Sayou Fabric에 오신 것을 환영합니다.\n"
        "이 문서는 스캔된 한국어 PDF입니다."
    )
    MockPilImg.open.return_value = MagicMock()

    doc_ocr = DocumentPipeline.process(
        JPEG_BYTES,
        "korean_scan.jpg",
        ocr={"lang": "kor"},
    )

page_ocr = doc_ocr.pages[0]
ocr_elems = [e for e in page_ocr.elements if isinstance(e, TextElement)]

print("\n=== Scanned Image with OCR ===")
print(f"  OCR elements: {len(ocr_elems)}")
if ocr_elems:
    print(f"  OCR text    : {ocr_elems[0].text[:80]!r}")
```

## RGBA / PNG Transparency Handling

Pillow cannot save RGBA images directly to PDF.  `ImageToPdfConverter`
composites RGBA images onto a white background before saving.
This is handled automatically — no configuration needed.

```python
print("\n=== RGBA Transparency Handling ===")
with patch("sayou.document.converter.image_converter.Image") as MockImg, patch(
    "sayou.document.parser.pdf_parser.fitz"
) as mock_fitz:

    rgba_img = MagicMock()
    rgba_img.mode = "RGBA"
    rgba_img.size = (800, 600)
    MockImg.open.return_value = rgba_img

    bg = MagicMock()
    bg.mode = "RGB"
    MockImg.new.return_value = bg
    bg.save.side_effect = lambda buf, fmt, **k: buf.write(b"%PDF-rgba")

    mock_fitz.TEXTFLAGS_DICT = 0
    fdoc3 = MagicMock()
    fdoc3.page_count = 1
    fdoc3.load_page.return_value = _make_pdf_page()
    fdoc3.get_toc.return_value = []
    mock_fitz.open.return_value = fdoc3

    PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
    doc_rgba = DocumentPipeline.process(PNG_BYTES, "transparent.png")

    MockImg.new.assert_called_once_with("RGB", (800, 600), (255, 255, 255))
    print("  RGBA composited onto white background: OK")
    print(f"  doc_type: {doc_rgba.doc_type}")
```

## Save Results

```python
output = doc_ocr.model_dump()
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nSaved Document to '{OUTPUT_FILE}'")
```