from typing import Any, List, Union

from sayou.core.registry import register_component
from sayou.core.schemas import SayouNode, SayouOutput
from sayou.core.vocabulary import SayouAttribute

from ..interfaces.base_adapter import BaseAdapter


@register_component("adapter")
class CodeChunkAdapter(BaseAdapter):
    """
    Adapter for Sayou Code Splitter results.

    Converts `SayouChunk` (Code) into `SayouNode`.
    Maps semantic types (class_header, method) to SayouClasses (CLASS, METHOD).
    Establishes hierarchical relationships (FILE -> CLASS -> METHOD).
    """

    component_name = "CodeChunkAdapter"
    SUPPORTED_TYPES = ["code_chunk"]

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        if strategy in cls.SUPPORTED_TYPES:
            return 1.0

        if isinstance(input_data, list) and len(input_data) > 0:
            first = input_data[0]
            if hasattr(first, "metadata") and (
                "extension" in first.metadata or "source" in first.metadata
            ):
                return 0.9
        return 0.0

    def _do_adapt(self, input_data: Union[List[Any], Any], **kwargs) -> SayouOutput:
        if not isinstance(input_data, list):
            input_data = [input_data]

        nodes = []

        # Source Path -> Node ID
        file_nodes_map = {}

        for chunk in input_data:
            # Chunk -> Dict
            chunk_data = chunk.model_dump() if hasattr(chunk, "model_dump") else chunk
            content = chunk_data.get("content", "")
            meta = chunk_data.get("metadata", {})

            # 1. Base Info
            source_path = meta.get("source", "unknown")
            chunk_idx = meta.get("chunk_index", 0)

            # 2. Node ID Generation (Deterministic)
            # sayou:code:<path>:<chunk_index>
            safe_path = source_path.replace("/", "_").replace(".", "_")
            node_id = f"sayou:code:{safe_path}:{chunk_idx}"

            # 3. Class & Attribute Mapping
            sem_type = meta.get("semantic_type", "code_block")

            if sem_type == "class_header":
                node_class = "sayou:Class"  # SayouClass.CLASS
                friendly_name = f"CLASS [{meta.get('class_name')}]"
            elif sem_type == "method":
                node_class = "sayou:Method"
                friendly_name = f"METHOD [{meta.get('function_name')}]"
            elif sem_type == "function":  # Top-level Function
                node_class = "sayou:Function"
                friendly_name = f"FUNC [{meta.get('function_name')}]"
            elif sem_type == "class_attributes":
                node_class = "sayou:AttributeBlock"
                friendly_name = f"ATTRS [{meta.get('parent_node')}]"
            else:
                node_class = "sayou:CodeBlock"
                friendly_name = f"CODE [{chunk_idx}]"

            attributes = {
                SayouAttribute.TEXT: content,
                "sayou:semanticType": sem_type,
                "sayou:filePath": source_path,
                "sayou:lineStart": meta.get("start_line"),
            }
            for k, v in meta.items():
                if k not in ["source", "chunk_index", "semantic_type"]:
                    attributes[f"meta:{k}"] = v

            # 4. Relationships (Parent Linking)
            relationships = {}

            # 4-1. File Relationship
            file_node_id = f"sayou:file:{safe_path}"
            relationships["sayou:definedIn"] = [file_node_id]

            if file_node_id not in file_nodes_map:
                file_nodes_map[file_node_id] = SayouNode(
                    node_id=file_node_id,
                    node_class="sayou:File",
                    friendly_name=f"FILE [{source_path}]",
                    attributes={"sayou:filePath": source_path},
                )

            # 4-2. Logical Parent (Method -> Class)
            if "parent_node" in meta:
                attributes["_hint_parent_class"] = meta["parent_node"]

            # 5. Create Node
            node = SayouNode(
                node_id=node_id,
                node_class=node_class,
                friendly_name=friendly_name,
                attributes=attributes,
                relationships=relationships,
            )
            nodes.append(node)

        all_nodes = list(file_nodes_map.values()) + nodes

        return SayouOutput(nodes=all_nodes, metadata={"source": "sayou-code-adapter"})
