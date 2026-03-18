import ast
import json
from typing import Any, Dict, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock, SayouChunk

from ..interfaces.base_splitter import BaseSplitter


@register_component("splitter")
class JsonSplitter(BaseSplitter):
    """
    (Specialized) Splitter for JSON structures (Dict/List).

    Unlike text-based splitters, this traverses the object tree.
    It groups list items or dictionary keys into chunks that respect
    JSON syntax and semantic boundaries.
    """

    component_name = "JsonSplitter"
    SUPPORTED_TYPES = ["json", "dict", "record", "list"]

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        if strategy in cls.SUPPORTED_TYPES:
            return 1.0

        if isinstance(input_data, SayouBlock):
            if input_data.type in ["json", "record"]:
                return 1.0
            if isinstance(input_data.content, (dict, list)):
                return 1.0

        return 0.0

    def _do_split(self, doc: SayouBlock) -> List[SayouChunk]:
        """
        Routes the split logic based on content type (List vs Dict).
        """
        config = doc.metadata.get("config", {})
        chunk_size = config.get("chunk_size", 100)
        min_chunk_size = config.get("min_chunk_size", 50)
        base_meta = doc.metadata.copy()

        data = doc.content

        if isinstance(data, str):
            try:
                parsed_data = json.loads(data)
            except json.JSONDecodeError:
                try:
                    parsed_data = ast.literal_eval(data)
                except (ValueError, SyntaxError):
                    return []
            data = parsed_data

        if isinstance(data, list):
            return self._split_json_list(data, chunk_size, min_chunk_size, base_meta)
        elif isinstance(data, dict):
            return self._split_json_dict_wrapper(data, chunk_size, base_meta)

        return []

    def _split_json_dict_wrapper(self, data, chunk_size, meta):
        try:
            json_str = json.dumps(data, ensure_ascii=False)
            if len(json_str) <= chunk_size:
                return [SayouChunk(content=json_str, metadata=meta)]
            return self._split_json_dict(data, chunk_size, meta)
        except Exception as e:
            self._log(f"Error handling dict: {e}")
            return []

    def _split_json_list(
        self, data_list: List[Any], chunk_size: int, min_chunk_size: int, meta: Dict
    ) -> List[SayouChunk]:
        """
        Groups list items into chunks until they reach chunk_size.
        """
        chunks = []
        current_batch = []
        current_size = 0
        start_idx = 0

        for i, item in enumerate(data_list):
            item_str = json.dumps(item, ensure_ascii=False)
            item_len = len(item_str)

            if item_len > chunk_size:
                if current_batch:
                    chunks.append(
                        self._create_chunk(current_batch, meta, start_idx, i - 1)
                    )
                    current_batch = []
                    current_size = 0

                if isinstance(item, dict):
                    sub_meta = meta.copy()
                    sub_meta["list_index"] = i
                    sub_chunks = self._split_json_dict(item, chunk_size, sub_meta)
                    chunks.extend(sub_chunks)
                else:
                    chunks.append(self._create_chunk([item], meta, i, i))

                start_idx = i + 1
                continue

            if current_size + item_len > chunk_size and current_batch:
                chunks.append(self._create_chunk(current_batch, meta, start_idx, i - 1))
                current_batch = []
                current_size = 0
                start_idx = i

            current_batch.append(item)
            current_size += item_len

        if current_batch:
            chunks.append(
                self._create_chunk(current_batch, meta, start_idx, len(data_list) - 1)
            )
        return chunks

    def _split_json_dict(
        self, data_dict: Dict[str, Any], chunk_size: int, meta: Dict
    ) -> List[SayouChunk]:
        """
        Splits a large dictionary by keys.
        If a value is a large list, it delegates to _split_json_list.
        """
        chunks = []
        current_batch = {}
        current_size = 0
        batch_idx = 0

        for key, value in data_dict.items():
            val_json = json.dumps(value, ensure_ascii=False)
            val_size = len(val_json)

            if val_size > chunk_size:
                if current_batch:
                    chunks.append(
                        self._create_obj_chunk(current_batch, meta, f"part_{batch_idx}")
                    )
                    current_batch = {}
                    current_size = 0
                    batch_idx += 1

                sub_meta = meta.copy()
                current_path = sub_meta.get("json_path", "")
                sub_meta["json_path"] = f"{current_path}.{key}" if current_path else key

                if isinstance(value, list):
                    sub_chunks = self._split_json_list(value, chunk_size, 0, sub_meta)
                    chunks.extend(sub_chunks)
                elif isinstance(value, dict):
                    sub_chunks = self._split_json_dict(value, chunk_size, sub_meta)
                    chunks.extend(sub_chunks)
                else:
                    chunks.append(
                        self._create_obj_chunk(
                            {key: value}, meta, f"large_val_{batch_idx}"
                        )
                    )

                continue

            kv_pair = {key: value}
            kv_len = len(json.dumps(kv_pair, ensure_ascii=False))

            if current_size + kv_len > chunk_size and current_batch:
                chunks.append(
                    self._create_obj_chunk(current_batch, meta, f"part_{batch_idx}")
                )
                current_batch = {}
                current_size = 0
                batch_idx += 1

            current_batch[key] = value
            current_size += kv_len

        if current_batch:
            chunks.append(
                self._create_obj_chunk(current_batch, meta, f"part_{batch_idx}")
            )

        return chunks

    def _create_chunk(
        self, batch: List, meta: Dict, start_idx: int, end_idx: int
    ) -> SayouChunk:
        """Helper for list chunks"""
        content_str = json.dumps(batch, ensure_ascii=False, indent=2)
        new_meta = meta.copy()
        new_meta.update(
            {
                "chunk_type": "json_list",
                "item_count": len(batch),
                "index_start": start_idx,
                "index_end": end_idx,
            }
        )
        if batch and isinstance(batch[0], dict) and "start" in batch[0]:
            new_meta["sayou:startTime"] = batch[0]["start"]
            new_meta["sayou:endTime"] = batch[-1].get("start", 0) + batch[-1].get(
                "duration", 0
            )
        return SayouChunk(content=content_str, metadata=new_meta)

    def _create_obj_chunk(self, batch: Dict, meta: Dict, suffix: str) -> SayouChunk:
        """Helper for dict chunks"""
        content_str = json.dumps(batch, ensure_ascii=False, indent=2)
        new_meta = meta.copy()
        new_meta["chunk_type"] = "json_object"
        new_meta["chunk_id_suffix"] = suffix
        return SayouChunk(content=content_str, metadata=new_meta)
