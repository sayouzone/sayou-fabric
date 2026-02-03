import os
from collections import defaultdict
from typing import Any, Dict

from sayou.core.ontology import SayouAttribute, SayouClass, SayouPredicate
from sayou.core.registry import register_component
from sayou.core.schemas import SayouOutput

from ..interfaces.base_builder import BaseBuilder


@register_component("builder")
class CodeGraphBuilder(BaseBuilder):
    """
    [DIAGNOSTIC MODE]
    Connects nodes and LOGS EVERY FAILURE detail.
    """

    component_name = "CodeGraphBuilder"
    SUPPORTED_TYPES = ["code_graph"]

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        if isinstance(input_data, SayouOutput) and input_data.nodes:
            return 1.0
        return 0.0

    def _do_build(self, data: SayouOutput, **kwargs) -> Dict[str, Any]:
        nodes = data.nodes
        edges_list = []
        nodes_map = {n.node_id: n.model_dump(exclude={"relationships"}) for n in nodes}

        self._log(f"🔥 [BUILD] Processing {len(nodes)} code nodes...")

        # -----------------------------------------------------
        # 1. Map Building (Indexing)
        # -----------------------------------------------------
        file_map = {}  # path -> file_node_id
        symbol_map = defaultdict(dict)  # path -> { symbol_name : node_id }

        for node in nodes:
            raw_path = node.attributes.get(
                SayouAttribute.FILE_PATH
            ) or node.attributes.get(SayouAttribute.SOURCE)

            if not raw_path:
                continue
            norm_path = raw_path.replace("\\", "/")

            # File Map
            if node.node_class == SayouClass.FILE:
                file_map[norm_path] = node.node_id
                no_ext = os.path.splitext(norm_path)[0]
                file_map[no_ext] = node.node_id

            # Symbol Map
            name = None
            if node.node_class == SayouClass.CLASS:
                name = node.attributes.get("meta:class_name")
            elif node.node_class in [SayouClass.FUNCTION, SayouClass.METHOD]:
                name = node.attributes.get("meta:function_name")

            if name:
                symbol_map[norm_path][name] = node.node_id
                no_ext = os.path.splitext(norm_path)[0]
                symbol_map[no_ext][name] = node.node_id

        self._log(
            f"📊 [INDEX] Files: {len(file_map)}, Symbols: {sum(len(v) for v in symbol_map.values())}"
        )

        # -----------------------------------------------------
        # 2. Connection Logic
        # -----------------------------------------------------
        for node in nodes:
            # (A) Symbol belongs to File (CONTAINS)
            if node.node_class != SayouClass.FILE:
                src = node.attributes.get(SayouAttribute.FILE_PATH)
                if src:
                    f_id = file_map.get(src.replace("\\", "/"))
                    if f_id:
                        edges_list.append(
                            {
                                "source": f_id,
                                "target": node.node_id,
                                "type": SayouPredicate.CONTAINS,
                            }
                        )

            # (B) Import Resolution (IMPORTS)
            imports = node.attributes.get("meta:imports", [])
            if not imports:
                continue

            src_path = node.attributes.get(
                SayouAttribute.FILE_PATH
            ) or node.attributes.get(SayouAttribute.SOURCE)
            if not src_path:
                continue

            src_path = src_path.replace("\\", "/")
            src_dir = os.path.dirname(src_path)

            for imp in imports:
                if not isinstance(imp, dict):
                    continue
                module = imp.get("module")
                name = imp.get("name")
                level = imp.get("level", 0)

                if not module:
                    continue

                target_file_path = self._debug_resolve_path(
                    module, level, src_dir, file_map
                )

                if target_file_path:
                    target_id = None
                    # 1. Try to link to specific Symbol
                    if name:
                        target_id = symbol_map[target_file_path].get(name)

                    # 2. Fallback to File
                    if not target_id:
                        target_id = file_map.get(target_file_path)

                    if target_id and target_id != node.node_id:
                        edges_list.append(
                            {
                                "source": node.node_id,
                                "target": target_id,
                                "type": SayouPredicate.IMPORTS,
                            }
                        )
                else:
                    pass

        self._log(f"✅ [BUILD] Generated {len(edges_list)} edges.")

        return {
            "nodes": list(nodes_map.values()),
            "edges": edges_list,
            "metadata": data.metadata,
        }

    def _debug_resolve_path(self, module, level, current_dir, file_map):
        if level > 0:
            target_dir = current_dir
            for _ in range(level - 1):
                target_dir = os.path.dirname(target_dir)
            sub = module.replace(".", "/") if module else ""
            guess = os.path.join(target_dir, sub).replace("\\", "/")

            if guess in file_map:
                return guess
            if f"{guess}/__init__" in file_map:
                return f"{guess}/__init__"
            return None
        else:
            suffix = module.replace(".", "/")
            for path in file_map.keys():
                if path.endswith(suffix):
                    return path
                if path.endswith(f"{suffix}/__init__"):
                    return path
            return None
