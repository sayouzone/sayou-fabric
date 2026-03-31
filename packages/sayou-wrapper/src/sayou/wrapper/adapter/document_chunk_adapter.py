import hashlib
import uuid
from typing import Any, List, Union

from sayou.core.ontology import SayouAttribute, SayouClass, SayouPredicate
from sayou.core.registry import register_component
from sayou.core.schemas import SayouNode, SayouOutput

from ..interfaces.base_adapter import BaseAdapter


@register_component("adapter")
class DocumentChunkAdapter(BaseAdapter):
    """
    Standard adapter for sayou-chunking results.

    Converts SayouChunk objects into semantic SayouNodes, mapping
    metadata fields (semantic_type, parent_id, …) to ontology classes
    and predicates.
    """

    component_name = "DocumentChunkAdapter"
    SUPPORTED_TYPES = ["document_chunk"]

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        if strategy in cls.SUPPORTED_TYPES:
            return 1.0

        if isinstance(input_data, list):
            if len(input_data) == 0:
                return 0.1
            first = input_data[0]
            if hasattr(first, "doc_type") or (
                isinstance(first, dict) and "chunk_id" in first
            ):
                return 0.95
            if isinstance(first, dict):
                return 0.6
            return 0.3

        if hasattr(input_data, "doc_type") or (
            isinstance(input_data, dict) and "chunk_id" in input_data
        ):
            return 0.95

        return 0.0

    def _do_adapt(self, input_data: Union[List[Any], Any]) -> SayouOutput:
        """
        Convert chunks into a list of SayouNodes.

        Handles both Pydantic Chunk objects and plain dicts.
        Node URIs are deterministic: derived from chunk IDs or content hash.

        Args:
            input_data: A single chunk or list of chunks.

        Returns:
            SayouOutput containing the constructed nodes.
        """
        if not isinstance(input_data, list):
            input_data = [input_data]

        nodes = []

        for item in input_data:
            chunk_data = item.model_dump() if hasattr(item, "model_dump") else item

            if not isinstance(chunk_data, dict):
                self._log(f"Skipping invalid chunk data: {type(item)}", level="warning")
                continue

            content = chunk_data.get("content", "")
            meta = chunk_data.get("metadata", {})

            # --- ID resolution ---
            raw_id = meta.get("chunk_id", "unknown")
            if not raw_id or raw_id == "unknown":
                raw_id = (
                    hashlib.md5(content.encode("utf-8")).hexdigest()
                    if content
                    else str(uuid.uuid4())
                )

            source_name = meta.get("filename") or meta.get("source")
            if source_name:
                safe_name = source_name.replace(" ", "_").replace(":", "")
                node_id = f"sayou:doc:{safe_name}:{raw_id}"
            else:
                node_id = f"sayou:doc:{raw_id}"

            # --- Node class from semantic type ---
            sem_type = meta.get("semantic_type", "text")
            is_header = meta.get("is_header", False)

            if is_header:
                node_class = SayouClass.TOPIC
            elif sem_type == "table":
                node_class = SayouClass.TABLE
            elif sem_type == "code_block":
                node_class = SayouClass.CODE_BLOCK
            elif sem_type == "list_item":
                node_class = SayouClass.LIST_ITEM
            else:
                node_class = SayouClass.TEXT_FRAGMENT

            # --- Attributes ---
            attributes = {
                SayouAttribute.TEXT: content,
                SayouAttribute.SEMANTIC_TYPE: sem_type,
                SayouAttribute.PAGE_INDEX: meta.get("page_num"),
                SayouAttribute.PART_INDEX: meta.get("part_index"),
                SayouAttribute.SOURCE: meta.get("source"),
            }
            # Preserve remaining metadata as passthrough attributes.
            for k, v in meta.items():
                if k not in {"chunk_id", "semantic_type", "parent_id", "is_header"}:
                    attributes[f"meta:{k}"] = v

            # --- Relationships ---
            relationships = {}
            raw_parent_id = meta.get("parent_id")

            if raw_parent_id:
                if source_name:
                    safe_name = source_name.replace(" ", "_").replace(":", "")
                    std_parent_id = f"sayou:doc:{safe_name}:{raw_parent_id}"
                else:
                    std_parent_id = f"sayou:doc:{raw_parent_id}"
                relationships[SayouPredicate.HAS_PARENT] = [std_parent_id]

            nodes.append(
                SayouNode(
                    node_id=node_id,
                    node_class=node_class,
                    friendly_name=f"DOC_NODE [{sem_type}] {raw_id}",
                    attributes=attributes,
                    relationships=relationships,
                )
            )

        return SayouOutput(nodes=nodes, metadata={"source": "sayou-chunking"})
