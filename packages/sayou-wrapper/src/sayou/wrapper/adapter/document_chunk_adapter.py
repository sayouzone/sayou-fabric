from typing import Any, List, Union

from ..core.schemas import SayouNode, WrapperOutput
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
                node_class = "sayou:Topic"
            elif sem_type == "table":
                node_class = "sayou:Table"
            elif sem_type == "code_block":
                node_class = "sayou:Code"
            elif sem_type == "list_item":
                node_class = "sayou:ListItem"
            else:
                node_class = "sayou:TextFragment"

            # 3. Attributes Mapping
            attributes = {
                "schema:text": content,
                "sayou:semanticType": sem_type,
                "sayou:pageIndex": meta.get("page_num"),
                "sayou:partIndex": meta.get("part_index"),
                "sayou:source": meta.get("source"),
            }

            # 4. Relationships Mapping
            relationships = {}
            parent_id = meta.get("parent_id")
            if parent_id:
                std_parent_id = f"sayou:doc:{parent_id}"
                relationships["sayou:hasParent"] = [std_parent_id]

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
