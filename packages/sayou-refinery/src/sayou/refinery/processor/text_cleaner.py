import re
from typing import List

from ..core.schemas import ContentBlock
from ..interfaces.base_processor import BaseProcessor


class TextCleaner(BaseProcessor):

    component_name = "TextCleaner"

    def initialize(
        self, patterns: List[str] = None, normalize_space: bool = True, **kwargs
    ):
        self.normalize_space = normalize_space
        self.patterns = [re.compile(p) for p in (patterns or [])]
        self._space_re = re.compile(r"[ \t]+")

    def _do_process(self, blocks: List[ContentBlock]) -> List[ContentBlock]:
        for block in blocks:
            if block.type not in ["text", "md"]:
                continue

            if not isinstance(block.content, str):
                continue

            text = block.content

            # 1. Custom Patterns Removal
            for pat in self.patterns:
                text = pat.sub("", text)

            # 2. Whitespace Normalization
            if self.normalize_space:
                text = self._space_re.sub(" ", text)

            block.content = text.strip()

        return blocks
