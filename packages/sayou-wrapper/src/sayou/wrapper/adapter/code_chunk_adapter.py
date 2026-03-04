"""
CodeChunkAdapter — SayouChunk (Code) → SayouNode

Improvements over the original
────────────────────────────────
1. CLASS → METHOD / CLASS_ATTRIBUTES hierarchy:
     class_header nodes now carry a  sayou:contains  relationship
     listing every child method / attribute block defined within them.
   Additionally, method nodes carry a  sayou:hasParent  pointing back to the
   class node. This makes the KG properly hierarchical instead of flat.

2. Stable node IDs:
     Methods are identified as  <file>::<ClassName>.<method_name>
     rather than the generic  <file>:<chunk_index>.
     This survives minor refactors (line numbers shift) and enables diff
     engines to track the same logical entity across versions.

3. Call-graph raw attributes are forwarded to node attributes so the
   downstream CodeGraphBuilder can resolve them into CALLS edges without
   needing to re-parse the source.

4. Standardised metadata keys are consumed correctly:
     lineStart / lineEnd  (produced by PythonSplitter and all stubs)
"""

import os
from collections import defaultdict
from typing import Any, Dict, List, Union

from sayou.core.ontology import SayouAttribute, SayouClass, SayouPredicate
from sayou.core.registry import register_component
from sayou.core.schemas import SayouNode, SayouOutput

from ..interfaces.base_adapter import BaseAdapter


@register_component("adapter")
class CodeChunkAdapter(BaseAdapter):
    """
    Converts code SayouChunks into a typed, hierarchical SayouOutput.

    Node ID convention
    ──────────────────
    File   : sayou:file:<safe_path>
    Class  : sayou:class:<safe_path>::<ClassName>
    Method : sayou:method:<safe_path>::<ClassName>.<method_name>
    Func   : sayou:func:<safe_path>::<function_name>
    Attrs  : sayou:attrs:<safe_path>::<ClassName>.attrs
    Block  : sayou:block:<safe_path>::<chunk_index>
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

    # ── main adaptation logic ─────────────────────────────────────────

    def _do_adapt(self, input_data: Union[List[Any], Any], **kwargs) -> SayouOutput:
        if not isinstance(input_data, list):
            input_data = [input_data]

        # ---- Pass 1: build all nodes, track class nodes by name ----
        file_nodes: Dict[str, SayouNode] = {}  # file_node_id → node
        class_nodes: Dict[str, SayouNode] = {}  # "<safe_path>::<ClassName>" → node

        # Gather child node IDs per class so we can build CONTAINS later.
        # class_children[class_key] = list of child node_ids
        class_children: Dict[str, List[str]] = defaultdict(list)

        all_nodes: List[SayouNode] = []

        for chunk in input_data:
            chunk_data = chunk.model_dump() if hasattr(chunk, "model_dump") else chunk
            content: str = chunk_data.get("content", "")
            meta: Dict[str, Any] = chunk_data.get("metadata", {})

            source_path = meta.get("source", "unknown")
            safe_path = self._safe(source_path)
            sem_type = meta.get("semantic_type", "code_block")

            # ---- Ensure file node ----
            file_node_id = f"sayou:file:{safe_path}"
            if file_node_id not in file_nodes:
                file_nodes[file_node_id] = SayouNode(
                    node_id=file_node_id,
                    node_class=SayouClass.FILE,
                    friendly_name=os.path.basename(source_path),
                    attributes={
                        SayouAttribute.FILE_PATH: source_path,
                        SayouAttribute.LANGUAGE: meta.get("language", ""),
                    },
                )

            # ---- Build typed node ----
            node = self._build_node(
                content,
                meta,
                source_path,
                safe_path,
                sem_type,
                file_node_id,
                class_nodes,
                class_children,
            )
            if node:
                all_nodes.append(node)

        # ---- Pass 2: inject CONTAINS edges into class nodes ----
        for class_key, child_ids in class_children.items():
            class_node = class_nodes.get(class_key)
            if class_node and child_ids:
                existing = class_node.relationships.get(SayouPredicate.CONTAINS, [])
                class_node.relationships[SayouPredicate.CONTAINS] = existing + child_ids

        final_nodes = list(file_nodes.values()) + list(class_nodes.values()) + all_nodes
        return SayouOutput(
            nodes=final_nodes,
            metadata={"source": "sayou-code-adapter"},
        )

    # ── node factory ──────────────────────────────────────────────────

    def _build_node(
        self,
        content: str,
        meta: Dict[str, Any],
        source_path: str,
        safe_path: str,
        sem_type: str,
        file_node_id: str,
        class_nodes: Dict[str, SayouNode],
        class_children: Dict[str, List[str]],
    ) -> SayouNode:

        line_start = meta.get("lineStart") or meta.get("start_line")
        line_end = meta.get("lineEnd") or meta.get("end_line")

        # ── class_header ─────────────────────────────────────────────
        if sem_type == "class_header":
            class_name = meta.get("class_name", "UnknownClass")
            class_key = f"{safe_path}::{class_name}"
            node_id = f"sayou:class:{class_key}"

            attrs = self._base_attrs(
                content, source_path, sem_type, line_start, line_end
            )
            attrs[SayouAttribute.SYMBOL_NAME] = class_name
            attrs[SayouAttribute.LANGUAGE] = meta.get("language", "")

            if meta.get("inherits_from"):
                attrs[SayouAttribute.INHERITS_FROM_RAW] = meta["inherits_from"]

            node = SayouNode(
                node_id=node_id,
                node_class=SayouClass.CLASS,
                friendly_name=class_name,
                attributes=attrs,
                relationships={SayouPredicate.DEFINED_IN: [file_node_id]},
            )
            # Register so child methods can back-reference this class
            class_nodes[class_key] = node
            return None  # returned via class_nodes, not all_nodes

        # ── method ───────────────────────────────────────────────────
        elif sem_type == "method":
            parent_class = meta.get("parent_node", "")
            func_name = meta.get("function_name", "unknown")
            class_key = f"{safe_path}::{parent_class}"
            node_id = f"sayou:method:{class_key}.{func_name}"

            attrs = self._base_attrs(
                content, source_path, sem_type, line_start, line_end
            )
            attrs[SayouAttribute.SYMBOL_NAME] = func_name
            attrs[SayouAttribute.PARENT_CLASS] = parent_class
            attrs[SayouAttribute.LANGUAGE] = meta.get("language", "")
            self._inject_call_attrs(attrs, meta)

            relationships = {SayouPredicate.DEFINED_IN: [file_node_id]}
            if class_key in {k for k in class_key.split("::")[-1:]}:
                pass  # class node link added after all nodes are built
            # Back-link to parent class (if it exists — it should, same pass)
            class_node_id = f"sayou:class:{class_key}"
            relationships[SayouPredicate.HAS_PARENT] = [class_node_id]

            class_children[class_key].append(node_id)

            return SayouNode(
                node_id=node_id,
                node_class=SayouClass.METHOD,
                friendly_name=func_name,
                attributes=attrs,
                relationships=relationships,
            )

        # ── function (top-level) ─────────────────────────────────────
        elif sem_type == "function":
            func_name = meta.get("function_name", "unknown")
            node_id = f"sayou:func:{safe_path}::{func_name}"

            attrs = self._base_attrs(
                content, source_path, sem_type, line_start, line_end
            )
            attrs[SayouAttribute.SYMBOL_NAME] = func_name
            attrs[SayouAttribute.LANGUAGE] = meta.get("language", "")
            self._inject_call_attrs(attrs, meta)

            return SayouNode(
                node_id=node_id,
                node_class=SayouClass.FUNCTION,
                friendly_name=func_name,
                attributes=attrs,
                relationships={SayouPredicate.DEFINED_IN: [file_node_id]},
            )

        # ── class_attributes ─────────────────────────────────────────
        elif sem_type == "class_attributes":
            parent_class = meta.get("parent_node", "")
            class_key = f"{safe_path}::{parent_class}"
            node_id = f"sayou:attrs:{class_key}.attrs"

            attrs = self._base_attrs(
                content, source_path, sem_type, line_start, line_end
            )
            attrs[SayouAttribute.PARENT_CLASS] = parent_class

            relationships = {SayouPredicate.DEFINED_IN: [file_node_id]}
            class_node_id = f"sayou:class:{class_key}"
            relationships[SayouPredicate.HAS_PARENT] = [class_node_id]

            class_children[class_key].append(node_id)

            return SayouNode(
                node_id=node_id,
                node_class=SayouClass.ATTRIBUTE_BLOCK,
                friendly_name=f"{parent_class}.attrs",
                attributes=attrs,
                relationships=relationships,
            )

        # ── generic code_block ────────────────────────────────────────
        else:
            chunk_idx = meta.get("chunk_index", 0)
            node_id = f"sayou:block:{safe_path}::{chunk_idx}"

            attrs = self._base_attrs(
                content, source_path, sem_type, line_start, line_end
            )
            attrs[SayouAttribute.LANGUAGE] = meta.get("language", "")

            # Loose blocks may carry import lists — preserve them
            if meta.get("imports"):
                attrs["sayou:importsRaw"] = meta["imports"]

            return SayouNode(
                node_id=node_id,
                node_class=SayouClass.CODE_BLOCK,
                friendly_name=f"Block:{chunk_idx}",
                attributes=attrs,
                relationships={SayouPredicate.DEFINED_IN: [file_node_id]},
            )

    # ── attribute helpers ─────────────────────────────────────────────

    def _base_attrs(
        self,
        content: str,
        source_path: str,
        sem_type: str,
        line_start,
        line_end,
    ) -> Dict[str, Any]:
        return {
            SayouAttribute.TEXT: content,
            SayouAttribute.FILE_PATH: source_path,
            SayouAttribute.SEMANTIC_TYPE: sem_type,
            SayouAttribute.LINE_START: line_start,
            SayouAttribute.LINE_END: line_end,
        }

    def _inject_call_attrs(self, attrs: Dict[str, Any], meta: Dict[str, Any]) -> None:
        """Forward call-graph raw data extracted by the language splitter."""
        if meta.get("calls"):
            attrs[SayouAttribute.CALLS_RAW] = meta["calls"]
        if meta.get("attribute_calls"):
            attrs[SayouAttribute.ATTR_CALLS_RAW] = meta["attribute_calls"]
        if meta.get("type_refs"):
            attrs[SayouAttribute.TYPE_REFS_RAW] = meta["type_refs"]

    @staticmethod
    def _safe(path: str) -> str:
        return path.replace("/", "_").replace("\\", "_").replace(".", "_")
