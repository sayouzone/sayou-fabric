from typing import Any, Dict, List

from ..core.schemas import ContentBlock
from ..interfaces.base_processor import BaseProcessor


class OutlierHandler(BaseProcessor):

    component_name = "OutlierHandler"

    def initialize(self, rules: Dict[str, Dict[str, Any]] = None, **kwargs):
        self.rules = rules or {}

    def _do_process(self, blocks: List[ContentBlock]) -> List[ContentBlock]:
        valid_blocks = []

        for block in blocks:
            if block.type != "record" or not isinstance(block.content, dict):
                valid_blocks.append(block)
                continue

            record = block.content
            should_drop = False

            for field, rule in self.rules.items():
                val = record.get(field)
                if val is None:
                    continue

                try:
                    val_f = float(val)
                    min_v = rule.get("min")
                    max_v = rule.get("max")
                    action = rule.get("action", "drop")

                    if min_v is not None and val_f < min_v:
                        if action == "drop":
                            should_drop = True
                            break
                        elif action == "clamp":
                            record[field] = min_v

                    if max_v is not None and val_f > max_v:
                        if action == "drop":
                            should_drop = True
                            break
                        elif action == "clamp":
                            record[field] = max_v

                except (ValueError, TypeError):
                    continue

            if not should_drop:
                block.content = record
                valid_blocks.append(block)

        return valid_blocks
