import io
try:
    from PIL import Image
except ImportError:
    Image = None

from ..interfaces.base_converter import BaseConverter
from ..core.exceptions import ConversionError

class ImageToPdfConverter(BaseConverter):
    """
    (Tier 2) Simple converter that turns Image files (JPG, PNG) into PDF bytes.
    Useful for unifying the pipeline input to PDF format.
    """
    component_name = "ImageToPdfConverter"
    SUPPORTED_TYPES = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]

    def _do_convert(self, file_bytes: bytes, file_name: str, **kwargs) -> bytes:
        if not Image:
            raise ImportError("Pillow is required for ImageToPdfConverter.")

        try:
            image = Image.open(io.BytesIO(file_bytes))
            
            # PDF 저장을 위해 RGB 모드로 변환 (PNG 투명도 이슈 방지)
            if image.mode in ("RGBA", "LA"):
                background = Image.new("RGB", image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                image = background
            elif image.mode != "RGB":
                image = image.convert("RGB")

            output_buffer = io.BytesIO()
            image.save(output_buffer, format="PDF", resolution=100.0)
            return output_buffer.getvalue()

        except Exception as e:
            raise ConversionError(f"Image conversion failed: {e}")