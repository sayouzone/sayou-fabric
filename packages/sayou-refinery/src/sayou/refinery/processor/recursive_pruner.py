from typing import Any, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock

from ..interfaces.base_processor import BaseProcessor


@register_component("processor")
class RecursivePruner(BaseProcessor):
    component_name = "RecursivePruner"

    @classmethod
    def can_handle(cls, blocks: list) -> float:
        if isinstance(blocks, list) and len(blocks) > 0:
            return 1.0
        return 0.0

    def _do_process(self, blocks: List[SayouBlock]) -> List[SayouBlock]:
        optimized_blocks = []

        for block in blocks:
            pruned_content = self._prune_empty(block.content)

            if pruned_content:
                block.content = pruned_content
                optimized_blocks.append(block)

        return optimized_blocks

    def _prune_empty(self, data: Any) -> Any:
        if isinstance(data, dict):
            cleaned_dict = {}
            for k, v in data.items():
                cleaned_v = self._prune_empty(v)
                if self._is_meaningful(cleaned_v):
                    cleaned_dict[k] = cleaned_v
            return cleaned_dict if cleaned_dict else None

        elif isinstance(data, list):
            cleaned_list = []
            for item in data:
                cleaned_item = self._prune_empty(item)
                if self._is_meaningful(cleaned_item):
                    cleaned_list.append(cleaned_item)
            return cleaned_list if cleaned_list else None

        else:
            if self._is_meaningful(data):
                return data
            return None

    def _is_meaningful(self, value: Any) -> bool:
        if value is None:
            return False
        if value == "":
            return False
        if isinstance(value, (list, dict)) and len(value) == 0:
            return False
        if isinstance(value, str) and value.upper() in ["NULL", "NONE", "NAN"]:
            return False

        return True
