from typing import Any, Dict, List

from ..core.exceptions import NormalizationError
from ..core.schemas import ContentBlock
from ..interfaces.base_normalizer import BaseNormalizer


class RecordNormalizer(BaseNormalizer):
    """
    (Tier 2) Converts structured data (Dict/List) into 'record' ContentBlocks.

    Suitable for processing database rows, CSV records, or JSON API responses.
    Each dictionary becomes a separate ContentBlock of type 'record'.
    """

    component_name = "RecordNormalizer"
    SUPPORTED_TYPES = ["json", "dict", "db_row", "record"]

    def _do_normalize(self, raw_data: Any) -> List[ContentBlock]:
        """
        Convert dict or list of dicts into record blocks.

        Args:
            raw_data (Any): A Dictionary or a List of Dictionaries.

        Returns:
            List[ContentBlock]: Blocks of type 'record'.
        """
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
        """
        Helper to wrap a single dictionary into a ContentBlock.

        Args:
            data (Dict[str, Any]): The data record.

        Returns:
            ContentBlock: A block with type='record' and content=data.
        """
        return ContentBlock(
            type="record",
            content=data,
            metadata={"fields": list(data.keys())},
        )
