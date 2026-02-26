import os
from typing import Any, List, Union

from sayou.core.ontology import SayouAttribute, SayouClass, SayouPredicate
from sayou.core.registry import register_component
from sayou.core.schemas import SayouNode, SayouOutput

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
        file_nodes_map = {}

        for chunk in input_data:
            chunk_data = chunk.model_dump() if hasattr(chunk, "model_dump") else chunk
            content = chunk_data.get("content", "")
            meta = chunk_data.get("metadata", {})

            source_path = meta.get("source", "unknown")
            chunk_idx = meta.get("chunk_index", 0)
            safe_path = source_path.replace("/", "_").replace(".", "_")
            node_id = f"sayou:code:{safe_path}:{chunk_idx}"

            # 3. Class Mapping (Logic using Ontology)
            sem_type = meta.get("semantic_type", "code_block")

            if sem_type == "class_header":
                node_class = SayouClass.CLASS
                friendly_name = meta.get("class_name")
            elif sem_type == "method":
                node_class = SayouClass.METHOD
                friendly_name = meta.get("function_name")
            elif sem_type == "function":
                node_class = SayouClass.FUNCTION
                friendly_name = meta.get("function_name")
            elif sem_type == "class_attributes":
                node_class = SayouClass.ATTRIBUTE_BLOCK
                friendly_name = "Attributes"
            else:
                node_class = SayouClass.CODE_BLOCK
                friendly_name = f"CodeBlock:{chunk_idx}"

            attributes = {
                SayouAttribute.TEXT: content,
                SayouAttribute.SEMANTIC_TYPE: sem_type,
                SayouAttribute.FILE_PATH: source_path,
                SayouAttribute.LINE_START: meta.get("start_line"),
                SayouAttribute.LINE_END: meta.get("end_line"),
            }

            for k, v in meta.items():
                if k not in ["source", "chunk_index", "semantic_type"]:
                    attributes[f"meta:{k}"] = v

            # 4. Relationships
            relationships = {}

            # File Node Linking
            file_node_id = f"sayou:file:{safe_path}"
            relationships[SayouPredicate.DEFINED_IN] = [file_node_id]

            if file_node_id not in file_nodes_map:
                file_nodes_map[file_node_id] = SayouNode(
                    node_id=file_node_id,
                    node_class=SayouClass.FILE,
                    friendly_name=os.path.basename(source_path),
                    attributes={SayouAttribute.FILE_PATH: source_path},
                )

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
