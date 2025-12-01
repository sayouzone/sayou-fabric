try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from typing import Any, List

from ..core.exceptions import NormalizationError
from ..core.schemas import ContentBlock
from ..interfaces.base_normalizer import BaseNormalizer


class HtmlTextNormalizer(BaseNormalizer):

    component_name = "HtmlTextNormalizer"
    SUPPORTED_TYPES = ["html"]

    def _do_normalize(self, raw_data: Any) -> List[ContentBlock]:
        if not BeautifulSoup:
            raise ImportError("BeautifulSoup4 is required for HtmlTextNormalizer.")

        if not isinstance(raw_data, str):
            raise NormalizationError(
                f"Input must be HTML string, got {type(raw_data)}."
            )

        soup = BeautifulSoup(raw_data, "html.parser")

        for tag in soup(["script", "style", "noscript", "iframe"]):
            tag.extract()

        text = soup.get_text(separator="\n")

        import re

        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        return [
            ContentBlock(type="text", content=text, metadata={"source_type": "html"})
        ]
