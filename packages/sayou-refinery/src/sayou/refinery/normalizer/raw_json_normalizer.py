from typing import Any, Dict, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock

from ..core.exceptions import NormalizationError
from ..interfaces.base_normalizer import BaseNormalizer


@register_component("normalizer")
class RawJsonNormalizer(BaseNormalizer):
    component_name = "RawJsonNormalizer"
    SUPPORTED_TYPES = ["raw_json"]

    @classmethod
    def can_handle(cls, raw_data: Any, strategy: str = "auto") -> float:
        if strategy in cls.SUPPORTED_TYPES:
            return 1.0

        if isinstance(raw_data, dict):
            return 0.85

        if isinstance(raw_data, list) and raw_data and isinstance(raw_data[0], dict):
            return 0.85

        return 0.0

    def _do_normalize(self, raw_data: Any) -> List[SayouBlock]:
        blocks = []
        safe_data = self._ensure_pure_structure(raw_data)

        if isinstance(safe_data, dict):
            blocks.append(self._create_block(safe_data))

        elif isinstance(safe_data, list):
            for item in safe_data:
                if isinstance(item, dict):
                    blocks.append(self._create_block(item))
                else:
                    self._log(
                        f"Skipping non-dict item in batch list: {type(item)}",
                        level="warning",
                    )

        else:
            raise NormalizationError(
                f"Raw JSON input must be a Dict or List[Dict], got {type(raw_data)}"
            )

        return blocks

    def _create_block(self, data: Dict[str, Any]) -> SayouBlock:
        metadata = {
            "source_type": "raw_json",
            "normalization_strategy": self.component_name,
        }

        return SayouBlock(type="record", content=data, metadata=metadata)

    def _ensure_pure_structure(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {k: self._ensure_pure_structure(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self._ensure_pure_structure(item) for item in data]
        return data
