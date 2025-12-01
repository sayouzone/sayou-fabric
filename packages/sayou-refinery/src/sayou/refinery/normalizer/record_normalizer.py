from typing import Any, Dict, List

from ..core.exceptions import NormalizationError
from ..core.schemas import ContentBlock
from ..interfaces.base_normalizer import BaseNormalizer


class RecordNormalizer(BaseNormalizer):

    component_name = "RecordNormalizer"
    SUPPORTED_TYPES = ["json", "dict", "db_row", "record"]

    def _do_normalize(self, raw_data: Any) -> List[ContentBlock]:
        blocks = []

        # Case 1: Single Dictionary
        if isinstance(raw_data, dict):
            blocks.append(self._create_block(raw_data))

        # Case 2: List of Dictionaries
        elif isinstance(raw_data, list):
            for item in raw_data:
                if isinstance(item, dict):
                    blocks.append(self._create_block(item))
                else:
                    self._log(
                        f"Skipping non-dict item in list: {type(item)}", level="warning"
                    )

        else:
            raise NormalizationError(
                f"Input must be Dict or List[Dict], got {type(raw_data)}"
            )

        return blocks

    def _create_block(self, data: Dict[str, Any]) -> ContentBlock:
        return ContentBlock(
            type="record",
            content=data,
            metadata={"fields": list(data.keys())},
        )
