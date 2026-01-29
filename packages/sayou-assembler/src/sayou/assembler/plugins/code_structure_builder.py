import os
from collections import defaultdict
from typing import Any, Dict

from sayou.core.registry import register_component
from sayou.core.schemas import SayouOutput
from ..interfaces.base_builder import BaseBuilder


@register_component("builder")
class CodeStructureBuilder(BaseBuilder):
    """
    [DIAGNOSTIC MODE]
    Connects nodes and LOGS EVERY FAILURE detail.
    """

    component_name = "CodeStructureBuilder"
    SUPPORTED_TYPES = ["code_structure"]

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        if isinstance(input_data, SayouOutput) and input_data.nodes:
            return 1.0
        return 0.0

    def _do_build(self, data: SayouOutput, **kwargs) -> Dict[str, Any]:
        nodes = data.nodes
        edges_list = []
        nodes_map = {n.node_id: n.model_dump(exclude={"relationships"}) for n in nodes}

        self._log(f"\n🔥🔥 [DIAGNOSTIC START] Processing {len(nodes)} nodes...")

        # -----------------------------------------------------
        # 1. Map Building & Inspection
        # -----------------------------------------------------
        file_map = {}  # path -> file_node_id
        symbol_map = defaultdict(dict)  # path -> { symbol_name : node_id }

        for node in nodes:
            raw_path = node.attributes.get("sayou:filePath") or node.attributes.get(
                "meta:source"
            )
            if not raw_path:
                continue

            norm_path = raw_path.replace("\\", "/")

            # File Map
            if node.node_class == "sayou:File":
                file_map[norm_path] = node.node_id
                no_ext = os.path.splitext(norm_path)[0]
                file_map[no_ext] = node.node_id

            # Symbol Map
            name = None
            if node.node_class == "sayou:Class":
                name = node.attributes.get("meta:class_name")
            elif node.node_class in ["sayou:Function", "sayou:Method"]:
                name = node.attributes.get("function_name")

            if name:
                symbol_map[norm_path][name] = node.node_id
                no_ext = os.path.splitext(norm_path)[0]
                symbol_map[no_ext][name] = node.node_id

        self._log(
            f"📊 [MAP STATS] Files: {len(file_map)}, Symbols indexed: {sum(len(v) for v in symbol_map.values())}"
        )
        # print(f"   (Sample File Key): {list(file_map.keys())[0] if file_map else 'None'}")

        # -----------------------------------------------------
        # 2. Connection Logic (With Detailed Logs)
        # -----------------------------------------------------
        for node in nodes:
            if node.node_class != "sayou:File":
                src = node.attributes.get("sayou:filePath")
                if src:
                    f_id = file_map.get(src.replace("\\", "/"))
                    if f_id:
                        edges_list.append(
                            {
                                "source": f_id,
                                "target": node.node_id,
                                "type": "sayou:contains",
                            }
                        )

            imports = node.attributes.get("meta:imports", [])
            if not imports:
                continue

            src_path = node.attributes.get("sayou:filePath") or node.attributes.get(
                "meta:source"
            )
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
                    reason = ""

                    if name:
                        target_id = symbol_map[target_file_path].get(name)
                        if not target_id:
                            reason = f"File found, but Symbol '{name}' NOT found in it."
                    else:
                        target_id = file_map.get(target_file_path)

                    if target_id and target_id != node.node_id:
                        edges_list.append(
                            {
                                "source": node.node_id,
                                "target": target_id,
                                "type": "sayou:imports",
                            }
                        )
                    else:
                        if "sayou" in src_path:
                            self._log(
                                f"❌ [SYM_FAIL] {os.path.basename(src_path)} imports '{name}' from '{module}'"
                            )
                            self._log(f"    -> Resolved File: {target_file_path}")
                            self._log(f"    -> Reason: {reason}")
                            self._log(
                                f"    -> Available Symbols in target: {list(symbol_map[target_file_path].keys())}"
                            )
                else:
                    if level > 0 or "sayou" in module:
                        self._log(
                            f"🚫 [PATH_FAIL] {os.path.basename(src_path)} imports '{module}' (lvl {level})"
                        )
                        self._log(f"    -> Current Dir: {src_dir}")

        self._log(f"🔥🔥 [DIAGNOSTIC END] Total Edges Generated: {len(edges_list)}\n")

        return {
            "nodes": list(nodes_map.values()),
            "edges": edges_list,
            "metadata": data.metadata,
        }

    def _debug_resolve_path(self, module, level, current_dir, file_map):
        # 1. Relative
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

            # self._log(f"    -> [Debug] Tried relative path: '{guess}' (Not found in map)")
            return None

        # 2. Absolute
        else:
            suffix = module.replace(".", "/")
            for path in file_map.keys():
                if path.endswith(suffix):
                    return path
                if path.endswith(f"{suffix}/__init__"):
                    return path

            # self._log(f"    -> [Debug] Tried suffix match: '{suffix}' (No match in map)")
            return None
