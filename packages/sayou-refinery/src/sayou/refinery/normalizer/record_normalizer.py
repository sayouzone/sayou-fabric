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

        safe_data = self._ensure_dict_structure(raw_data)

        # Case 1: Single Dictionary
        if isinstance(safe_data, dict):
            blocks.append(self._create_optimized_block(safe_data))

        # Case 2: List of Dictionaries
        elif isinstance(safe_data, list):
            if safe_data and isinstance(safe_data[0], dict):
                blocks.append(self._create_list_block(safe_data))
            else:
                for item in safe_data:
                    if isinstance(item, dict):
                        blocks.append(self._create_block(item))
                    else:
                        self._log(
                            f"Skipping non-dict item: {type(item)}", level="warning"
                        )

        else:
            raise NormalizationError(
                f"Input must be Dict or List[Dict], got {type(raw_data)}"
            )

        return blocks

    def _create_optimized_block(self, data: Dict[str, Any]) -> SayouBlock:
        """
        Separates heavy list content from metadata.
        """
        extracted_meta = {}
        if "meta" in data:
            extracted_meta.update(data["meta"])
        elif "metadata" in data:
            extracted_meta.update(data["metadata"])

        content_candidate = None
        dominant_key = None

        if "content" in data and ("meta" in data or "metadata" in data):
            content_candidate = data["content"]
        else:
            candidates = {}
            others = {}
            for k, v in data.items():
                if k in ["meta", "metadata"]:
                    continue
                if isinstance(v, list) and len(v) > 0:
                    candidates[k] = v
                else:
                    others[k] = v

            if len(candidates) == 1:
                dominant_key = list(candidates.keys())[0]
                content_candidate = candidates[dominant_key]
                extracted_meta.update(others)
                extracted_meta["content_key"] = dominant_key
            else:
                content_candidate = data.copy()
                content_candidate.pop("meta", None)
                content_candidate.pop("metadata", None)

        # ID Extraction
        id_candidates = ["id", "_id", "uuid", "video_id", "uid", "original_id"]
        found_id = None
        for key in id_candidates:
            if key in extracted_meta:
                found_id = extracted_meta[key]
                break
        if found_id:
            extracted_meta["original_id"] = str(found_id)

        final_content = self._ensure_dict_structure(content_candidate)

        return SayouBlock(type="record", content=final_content, metadata=extracted_meta)

    def _ensure_dict_structure(self, data: Any) -> Any:
        """
        Recursively convert Pydantic models, Objects, Lists, and Dicts into pure JSON types.
        """

        # 1. List
        if isinstance(data, list):
            return [self._ensure_dict_structure(item) for item in data]
        # 2. Dict
        if isinstance(data, dict):
            return {k: self._ensure_dict_structure(v) for k, v in data.items()}
        # Pydantic v2
        if hasattr(data, "model_dump") and callable(data.model_dump):
            return data.model_dump()
        # Pydantic v1
        if hasattr(data, "dict") and callable(data.dict):
            return data.dict()
        # General Object
        if hasattr(data, "__dict__"):
            return data.__dict__

        return data

    def _create_list_block(self, data_list: List[Dict]) -> SayouBlock:
        """
        [New] Creates a single block containing a list of records.
        Useful for YouTube transcripts where we want batch processing.
        """
        extracted_meta = {
            "record_count": len(data_list),
            "data_type": "list_of_records",
        }

        if data_list and "video_id" in data_list[0]:
            extracted_meta["video_id"] = data_list[0]["video_id"]

        return SayouBlock(
            type="record",
            content=data_list,
            metadata=extracted_meta,
        )

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
        if "meta" in data:
            extracted_meta.update(data["meta"])
        elif "metadata" in data:
            extracted_meta.update(data["metadata"])

        # 2. Content Decision
        if "content" in data and ("meta" in data or "metadata" in data):
            final_content = data["content"]
        else:
            final_content = data.copy()
            final_content.pop(
                "meta",
                None,
            )
            final_content.pop("metadata", None)

        # 3. ID Extraction
        id_candidates = ["id", "_id", "uuid", "video_id", "uid"]
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

        # 4. JSON Serialization check
        final_content = self._ensure_dict_structure(final_content)

        return SayouBlock(
            type="record",
            content=final_content,
            metadata=extracted_meta,
        )
