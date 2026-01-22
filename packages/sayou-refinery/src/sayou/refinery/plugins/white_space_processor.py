import re
from typing import Any, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock

from ..interfaces.base_processor import BaseProcessor


@register_component("processor")
class WhiteSpaceProcessor(BaseProcessor):
    """
    Cleans up excessive whitespace, newlines, and invisible characters.
    Essential for improving embedding quality and reducing token usage.
    """

    component_name = "WhiteSpaceProcessor"

    def _do_process(self, blocks: List[SayouBlock]) -> List[SayouBlock]:
        preserve_newlines = self.config.get("preserve_newlines", True)

        for block in blocks:
            if block.type == "text" and isinstance(block.content, str):
                block.content = self._clean_text(block.content, preserve_newlines)

            elif block.type == "record" and isinstance(block.content, dict):
                for k, v in block.content.items():
                    if isinstance(v, str):
                        block.content[k] = self._clean_text(v, preserve_newlines)

        return blocks

    def _clean_text(self, text: str, preserve_newlines: bool) -> str:
        if not text:
            return ""

        # 1. Replace unicode whitespace (e.g., \xa0, \u200b) with regular space
        text = text.replace("\xa0", " ").replace("\u200b", "")

        if preserve_newlines:
            # 2-A. Preserve newlines, limit consecutive spaces to 1, limit consecutive newlines to 2
            # (Preserve paragraphs, remove unnecessary whitespace)
            text = re.sub(r"[ \t]+", " ", text)  # Tab/Space -> 1 space
            text = re.sub(r"\n\s*\n", "\n\n", text)  # 3+ newlines -> 2 newlines
        else:
            # 2-B. Replace all newlines with spaces (complete single line text)
            text = re.sub(r"\s+", " ", text)

        return text.strip()
