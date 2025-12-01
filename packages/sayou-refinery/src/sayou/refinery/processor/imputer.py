from typing import Any, Dict, List

from ..core.schemas import ContentBlock
from ..interfaces.base_processor import BaseProcessor


class Imputer(BaseProcessor):
    component_name = "Imputer"

    def initialize(self, rules: Dict[str, Any] = None, **kwargs):
        self.rules = rules or {}
        if not self.rules:
            self._log("Imputer initialized with no rules.", level="warning")

    def _do_process(self, blocks: List[ContentBlock]) -> List[ContentBlock]:
        for block in blocks:
            if block.type != "record" or not isinstance(block.content, dict):
                continue

            record = block.content

            for field, default_value in self.rules.items():
                if record.get(field) is None:
                    record[field] = default_value

            block.content = record

        return blocks
