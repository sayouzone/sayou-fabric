from typing import Any, List, Union

from ..core.schemas import SayouNode, WrapperOutput
from ..core.vocabulary import SayouAttribute, SayouClass, SayouPredicate
from ..interfaces.base_adapter import BaseAdapter


class DocumentChunkAdapter(BaseAdapter):
    """
    Standard Adapter for Sayou Chunking results.
    Converts Chunks into semantic SayouNodes (Topic, Table, Code, TextFragment).
    """

    component_name = "DocumentChunkAdapter"
    SUPPORTED_TYPES = ["document_chunk"]

    def _do_adapt(self, input_data: Union[List[Any], Any]) -> WrapperOutput:
        if not isinstance(input_data, list):
            input_data = [input_data]

        nodes = []

        for item in input_data:
            chunk_data = item.model_dump() if hasattr(item, "model_dump") else item

            if not isinstance(chunk_data, dict):
                self._log(f"Skipping invalid chunk data: {type(item)}", level="warning")
                continue

            content = chunk_data.get("chunk_content") or chunk_data.get("content", "")
            meta = chunk_data.get("metadata", {})

            # 1. ID Mapping (Prefix 'sayou:doc:' added)
            raw_id = meta.get("chunk_id", "unknown")
            node_id = f"sayou:doc:{raw_id}"

            # 2. Node Class Decision (Semantic Type Mapping)
            sem_type = meta.get("semantic_type", "text")
            is_header = meta.get("is_header", False)

            if is_header:
                node_class = SayouClass.TOPIC
            elif sem_type == "table":
                node_class = SayouClass.TABLE
            elif sem_type == "code_block":
                node_class = SayouClass.CODE
            elif sem_type == "list_item":
                node_class = SayouClass.LIST_ITEM
            else:
                node_class = SayouClass.TEXT

            # [Refactored] Attributes using Constants
            attributes = {
                SayouAttribute.TEXT: content,
                SayouAttribute.SEMANTIC_TYPE: sem_type,
                SayouAttribute.PAGE_INDEX: meta.get("page_num"),
                SayouAttribute.PART_INDEX: meta.get("part_index"),
                SayouAttribute.SOURCE: meta.get("source"),
            }

            # 4. Relationships Mapping
            relationships = {}
            parent_id = meta.get("parent_id")
            if parent_id:
                std_parent_id = f"sayou:doc:{parent_id}"
                relationships[SayouPredicate.HAS_PARENT] = [std_parent_id]

            # 5. Create Node
            node = SayouNode(
                node_id=node_id,
                node_class=node_class,
                friendly_name=f"DOC_NODE [{sem_type}] {raw_id}",
                attributes=attributes,
                relationships=relationships,
            )
            nodes.append(node)

        return WrapperOutput(nodes=nodes, metadata={"source_system": "sayou-chunking"})
