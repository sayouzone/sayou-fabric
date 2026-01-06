from typing import Any, Dict, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock

from ..core.exceptions import NormalizationError
from ..interfaces.base_normalizer import BaseNormalizer


@register_component("normalizer")
class RecordNormalizer(BaseNormalizer):
    """
    (Tier 2) Converts structured data (Dict/List) into 'record' SayouBlocks.

    Suitable for processing database rows, CSV records, or JSON API responses.
    Each dictionary becomes a separate SayouBlock of type 'record'.
    """

    component_name = "RecordNormalizer"
    SUPPORTED_TYPES = ["json", "dict", "db_row", "record"]

    @classmethod
    def can_handle(cls, raw_data: Any, strategy: str = "auto") -> float:
        if strategy in ["json", "record", "db", "dict"]:
            return 1.0

        if isinstance(raw_data, dict):
            return 0.9
        if isinstance(raw_data, list):
            if len(raw_data) > 0 and isinstance(raw_data[0], dict):
                return 0.9

        return 0.0

    def _do_normalize(self, raw_data: Any) -> List[SayouBlock]:
        """
        Convert dict or list of dicts into record blocks.

        Args:
            raw_data (Any): A Dictionary or a List of Dictionaries.

        Returns:
            List[SayouBlock]: Blocks of type 'record'.
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
                    self._log(f"Skipping non-dict item: {type(item)}", level="warning")

        else:
            raise NormalizationError(
                f"Input must be Dict or List[Dict], got {type(raw_data)}"
            )

        return blocks

    def _create_block(self, data: Dict[str, Any]) -> SayouBlock:
        """
        Helper to wrap a single dictionary into a SayouBlock.

        Args:
            data (Dict[str, Any]): The data record.

        Returns:
            SayouBlock: A block with type='record' and content=data.
        """
        # 1. Meta Data Extraction
        extracted_meta = {}

        if "meta" in data and isinstance(data["meta"], dict):
            extracted_meta.update(data["meta"])
        elif "metadata" in data and isinstance(data["metadata"], dict):
            extracted_meta.update(data["metadata"])

        # 2. Content Decision
        if "content" in data and ("meta" in data or "metadata" in data):
            final_content = data["content"]
        else:
            final_content = data.copy()
            final_content.pop("meta", None)
            final_content.pop("metadata", None)

        # 3. Auto ID Extraction
        id_candidates = ["id", "_id", "uuid", "video_id", "uid", "no"]
        found_id = None

        for key in id_candidates:
            if key in extracted_meta:
                found_id = extracted_meta[key]
                break

        if not found_id and isinstance(final_content, dict):
            for key in id_candidates:
                if key in final_content:
                    found_id = final_content[key]
                    break

        if found_id:
            extracted_meta["original_id"] = str(found_id)

        # 4. Field Information Recording (Schema Discovery)
        if isinstance(final_content, dict):
            extracted_meta["fields"] = list(final_content.keys())

        return SayouBlock(
            type="record",
            content=final_content,
            metadata=extracted_meta,
        )
