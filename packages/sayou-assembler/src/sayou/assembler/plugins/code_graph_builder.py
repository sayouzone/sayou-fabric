"""
CodeGraphBuilder — assembles SayouNodes into a full code knowledge graph.

Edge types produced
────────────────────
CONTAINS      FILE → CLASS/FUNCTION/METHOD/BLOCK  (structural)
              CLASS → METHOD/ATTRIBUTE_BLOCK       (structural)

IMPORTS       BLOCK → FILE/SYMBOL                 (resolved import statement)

CALLS         FUNC/METHOD → FUNC/METHOD            (direct call, resolved)
              confidence: HIGH, resolution: DIRECT

MAYBE_CALLS   FUNC/METHOD → FUNC/METHOD            (duck-typing / attr call,
              confidence: LOW,  resolution: HEURISTIC   unresolved receiver)

INHERITS      CLASS → CLASS                        (resolved base class)
              confidence: HIGH, resolution: DIRECT

OVERRIDES     METHOD → METHOD                      (same name, child overrides
              confidence: HIGH, resolution: INFERRED   parent method)

USES_TYPE     FUNC/METHOD → CLASS                  (annotation / isinstance ref)
              confidence: MEDIUM, resolution: INFERRED

Design notes
────────────
• All index structures are built first in a single O(n) pass (Phase 1).
• Edge generation is a second O(n) pass over every node (Phase 2).
• `maybe_calls` only fires when the attribute-call name is unambiguous
  (appears in exactly one file's symbol map). Ambiguous names are skipped
  to avoid noise.
• Package-root detection: the builder accepts an optional `package_roots`
  kwarg (list of directory paths) to anchor absolute import resolution.
"""

import os
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set

from sayou.core.ontology import (SayouAttribute, SayouClass, SayouEdgeMeta,
                                 SayouPredicate)
from sayou.core.registry import register_component
from sayou.core.schemas import SayouOutput

from ..interfaces.base_builder import BaseBuilder


@register_component("builder")
class CodeGraphBuilder(BaseBuilder):
    """
    Connects all code nodes with typed, confidence-annotated edges.
    """

    component_name = "CodeGraphBuilder"
    SUPPORTED_TYPES = ["code_graph", "code_structure"]

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        if strategy in cls.SUPPORTED_TYPES:
            return 1.0
        if isinstance(input_data, SayouOutput) and input_data.nodes:
            return 1.0
        return 0.0

    # ── main build ────────────────────────────────────────────────────

    def _do_build(self, data: SayouOutput, **kwargs) -> Dict[str, Any]:
        nodes = data.nodes
        package_roots: List[str] = kwargs.get("package_roots", [])

        self._log(f"🔥 [BUILD] {len(nodes)} nodes incoming")

        # ── Phase 1: Index ────────────────────────────────────────────
        idx = self._build_index(nodes)
        self._log(
            f"📊 [INDEX] files={len(idx.file_map)}, "
            f"symbols={sum(len(v) for v in idx.symbol_map.values())}, "
            f"classes={sum(len(v) for v in idx.class_map.values())}"
        )

        # ── Phase 2: Edges ────────────────────────────────────────────
        edges: List[Dict[str, Any]] = []

        for node in nodes:
            self._edge_contains(node, idx, edges)
            self._edge_imports(node, idx, edges, package_roots)
            self._edge_calls(node, idx, edges)
            self._edge_maybe_calls(node, idx, edges)
            self._edge_inherits(node, idx, edges)
            self._edge_uses_type(node, idx, edges)

        self._edge_overrides(nodes, idx, edges)

        self._log(f"✅ [BUILD] {len(edges)} edges generated.")

        nodes_out = {n.node_id: n.model_dump(exclude={"relationships"}) for n in nodes}
        # Merge node-level relationships from Pass 1 (CONTAINS, HAS_PARENT)
        for node in nodes:
            for pred, targets in (node.relationships or {}).items():
                for t in targets:
                    edges.append(
                        _edge(node.node_id, t, pred, "HIGH", "DIRECT", "node_rel")
                    )

        return {
            "nodes": list(nodes_out.values()),
            "edges": edges,
            "metadata": data.metadata,
        }

    # ── index builder ─────────────────────────────────────────────────

    def _build_index(self, nodes) -> "_Index":
        idx = _Index()

        for node in nodes:
            fp = _norm(
                node.attributes.get(SayouAttribute.FILE_PATH)
                or node.attributes.get(SayouAttribute.SOURCE)
                or ""
            )
            if not fp:
                continue

            # file_map: full path AND path-without-extension
            if node.node_class == SayouClass.FILE:
                idx.file_map[fp] = node.node_id
                idx.file_map[_no_ext(fp)] = node.node_id

            # symbol_map: path → {symbol_name: node_id}
            sym = node.attributes.get(SayouAttribute.SYMBOL_NAME)
            if sym:
                idx.symbol_map[fp][sym] = node.node_id
                idx.symbol_map[_no_ext(fp)][sym] = node.node_id
                # Also index by symbol alone (for cross-file heuristics)
                idx.global_symbol_map[sym].append((fp, node.node_id))

            # class_map: path → {class_name: {method_name: node_id}}
            if node.node_class == SayouClass.CLASS:
                class_name = node.attributes.get(SayouAttribute.SYMBOL_NAME, "")
                idx.class_map[fp][class_name] = node.node_id
                idx.class_node_map[fp][class_name] = node

            if node.node_class == SayouClass.METHOD:
                parent = node.attributes.get(SayouAttribute.PARENT_CLASS, "")
                method = node.attributes.get(SayouAttribute.SYMBOL_NAME, "")
                idx.method_map[fp][parent][method] = node.node_id

        return idx

    # ── edge generators ───────────────────────────────────────────────

    def _edge_contains(self, node, idx: "_Index", edges: list) -> None:
        """FILE → everything else that lives in it."""
        if node.node_class == SayouClass.FILE:
            return
        fp = _norm(node.attributes.get(SayouAttribute.FILE_PATH, ""))
        if not fp:
            return
        fid = idx.file_map.get(fp)
        if fid:
            edges.append(
                _edge(
                    fid,
                    node.node_id,
                    SayouPredicate.CONTAINS,
                    "HIGH",
                    "DIRECT",
                    "structural",
                )
            )

    def _edge_imports(
        self, node, idx: "_Index", edges: list, package_roots: List[str]
    ) -> None:
        """Resolve import lists attached to code_block / function nodes."""
        raw_imports = node.attributes.get("sayou:importsRaw", [])
        if not raw_imports:
            return

        src_path = _norm(node.attributes.get(SayouAttribute.FILE_PATH, ""))
        src_dir = os.path.dirname(src_path)

        for imp in raw_imports:
            if not isinstance(imp, dict):
                continue
            module = imp.get("module", "")
            name = imp.get("name")
            level = imp.get("level", 0)

            target_path = self._resolve_import(
                module, level, src_dir, imp, idx, package_roots
            )

            if not target_path:
                continue

            target_id = None
            if name:
                target_id = idx.symbol_map[target_path].get(name)
            if not target_id:
                target_id = idx.file_map.get(target_path)

            if target_id and target_id != node.node_id:
                edges.append(
                    _edge(
                        node.node_id,
                        target_id,
                        SayouPredicate.IMPORTS,
                        "HIGH",
                        "DIRECT",
                        "import_resolver",
                    )
                )

    def _edge_calls(self, node, idx: "_Index", edges: list) -> None:
        """FUNC/METHOD → FUNC/METHOD via direct call names (CALLS, HIGH)."""
        if node.node_class not in (SayouClass.FUNCTION, SayouClass.METHOD):
            return

        raw_calls: List[str] = node.attributes.get(SayouAttribute.CALLS_RAW, [])
        if not raw_calls:
            return

        src_fp = _norm(node.attributes.get(SayouAttribute.FILE_PATH, ""))
        parent_class = node.attributes.get(SayouAttribute.PARENT_CLASS, "")

        for name in raw_calls:
            target_id = self._resolve_call(name, src_fp, parent_class, idx)
            if target_id and target_id != node.node_id:
                edges.append(
                    _edge(
                        node.node_id,
                        target_id,
                        SayouPredicate.CALLS,
                        "HIGH",
                        "DIRECT",
                        "call_resolver",
                    )
                )

    def _edge_maybe_calls(self, node, idx: "_Index", edges: list) -> None:
        """
        FUNC/METHOD → FUNC/METHOD via attribute call names (MAYBE_CALLS, LOW).

        `obj.method()` — we know the method name but not the receiver type.
        We only emit an edge when the name maps to exactly one known symbol
        (unambiguous). If multiple classes define the same method name, we
        skip it (too noisy).
        """
        if node.node_class not in (SayouClass.FUNCTION, SayouClass.METHOD):
            return

        attr_calls: List[str] = node.attributes.get(SayouAttribute.ATTR_CALLS_RAW, [])
        if not attr_calls:
            return

        src_fp = _norm(node.attributes.get(SayouAttribute.FILE_PATH, ""))

        for name in attr_calls:
            hits = idx.global_symbol_map.get(name, [])
            if len(hits) == 1:
                _, target_id = hits[0]
                if target_id != node.node_id:
                    edges.append(
                        _edge(
                            node.node_id,
                            target_id,
                            SayouPredicate.MAYBE_CALLS,
                            "LOW",
                            "HEURISTIC",
                            "duck_type_resolver",
                        )
                    )
            # >1 hits → ambiguous, skip

    def _edge_inherits(self, node, idx: "_Index", edges: list) -> None:
        """CLASS → CLASS via inherits_from_raw (INHERITS, HIGH)."""
        if node.node_class != SayouClass.CLASS:
            return

        raw: List[str] = node.attributes.get(SayouAttribute.INHERITS_FROM_RAW, [])
        if not raw:
            return

        src_fp = _norm(node.attributes.get(SayouAttribute.FILE_PATH, ""))

        for base_name in raw:
            # Simple name: look in same file first, then globally
            target_id = idx.class_map.get(src_fp, {}).get(
                base_name
            ) or self._global_class_lookup(base_name, idx)
            if target_id and target_id != node.node_id:
                edges.append(
                    _edge(
                        node.node_id,
                        target_id,
                        SayouPredicate.INHERITS,
                        "HIGH",
                        "DIRECT",
                        "inheritance_resolver",
                    )
                )

    def _edge_overrides(self, nodes, idx: "_Index", edges: list) -> None:
        """
        METHOD → METHOD (OVERRIDES) when a child class redefines a parent method.

        Algorithm:
          For every INHERITS edge already queued, look up child class methods
          and parent class methods. When names match → OVERRIDES edge.

        This runs after all nodes are indexed, as a separate pass.
        """
        # Collect (child_class_node_id, parent_class_node_id) pairs
        inherits_pairs: List[tuple] = []
        for node in nodes:
            if node.node_class != SayouClass.CLASS:
                continue
            raw = node.attributes.get(SayouAttribute.INHERITS_FROM_RAW, [])
            src_fp = _norm(node.attributes.get(SayouAttribute.FILE_PATH, ""))
            child_name = node.attributes.get(SayouAttribute.SYMBOL_NAME, "")
            for base_name in raw:
                parent_node = idx.class_node_map.get(src_fp, {}).get(
                    base_name
                ) or self._global_class_node_lookup(base_name, idx)
                if parent_node:
                    inherits_pairs.append((src_fp, child_name, parent_node))

        for child_fp, child_class, parent_node in inherits_pairs:
            parent_fp = _norm(parent_node.attributes.get(SayouAttribute.FILE_PATH, ""))
            parent_class = parent_node.attributes.get(SayouAttribute.SYMBOL_NAME, "")

            child_methods = idx.method_map.get(child_fp, {}).get(child_class, {})
            parent_methods = idx.method_map.get(parent_fp, {}).get(parent_class, {})

            for method_name, child_mid in child_methods.items():
                parent_mid = parent_methods.get(method_name)
                if parent_mid:
                    edges.append(
                        _edge(
                            child_mid,
                            parent_mid,
                            SayouPredicate.OVERRIDES,
                            "HIGH",
                            "INFERRED",
                            "override_resolver",
                        )
                    )

    def _edge_uses_type(self, node, idx: "_Index", edges: list) -> None:
        """FUNC/METHOD → CLASS via type annotation / isinstance refs (USES_TYPE)."""
        if node.node_class not in (SayouClass.FUNCTION, SayouClass.METHOD):
            return

        type_refs: List[str] = node.attributes.get(SayouAttribute.TYPE_REFS_RAW, [])
        if not type_refs:
            return

        src_fp = _norm(node.attributes.get(SayouAttribute.FILE_PATH, ""))

        for name in type_refs:
            target_id = idx.class_map.get(src_fp, {}).get(
                name
            ) or self._global_class_lookup(name, idx)
            if target_id and target_id != node.node_id:
                edges.append(
                    _edge(
                        node.node_id,
                        target_id,
                        SayouPredicate.USES_TYPE,
                        "MEDIUM",
                        "INFERRED",
                        "type_ref_resolver",
                    )
                )

    # ── resolution helpers ────────────────────────────────────────────

    def _resolve_call(
        self, name: str, src_fp: str, parent_class: str, idx: "_Index"
    ) -> Optional[str]:
        """
        Resolution order:
          1. Same-class method (for intra-class self.foo() calls)
          2. Same-file function
          3. Global unique symbol
        """
        # 1. Sibling method in same class
        if parent_class:
            mid = idx.method_map.get(src_fp, {}).get(parent_class, {}).get(name)
            if mid:
                return mid

        # 2. Same-file symbol (function or class)
        sid = idx.symbol_map.get(src_fp, {}).get(name)
        if sid:
            return sid

        # 3. Global unique
        hits = idx.global_symbol_map.get(name, [])
        if len(hits) == 1:
            return hits[0][1]

        return None

    def _resolve_import(
        self,
        module: str,
        level: int,
        src_dir: str,
        imp: dict,
        idx: "_Index",
        package_roots: List[str],
    ) -> Optional[str]:
        if level > 0:
            # Relative import
            target_dir = src_dir
            for _ in range(level - 1):
                target_dir = os.path.dirname(target_dir)
            sub = module.replace(".", "/") if module else ""
            guess = _norm(os.path.join(target_dir, sub))
            return self._match_file_map(guess, idx)
        else:
            # Absolute import — try package roots, then suffix matching
            suffix = module.replace(".", "/")
            for root in package_roots:
                candidate = _norm(os.path.join(root, suffix))
                result = self._match_file_map(candidate, idx)
                if result:
                    return result
            # Fallback: suffix scan
            for path in idx.file_map:
                if path.endswith(suffix) or path.endswith(f"{suffix}/__init__"):
                    return path
            return None

    def _match_file_map(self, guess: str, idx: "_Index") -> Optional[str]:
        if guess in idx.file_map:
            return guess
        if f"{guess}/__init__" in idx.file_map:
            return f"{guess}/__init__"
        return None

    def _global_class_lookup(self, name: str, idx: "_Index") -> Optional[str]:
        """Return class node_id if name is unambiguous across all files."""
        hits = [
            nid
            for fp, classes in idx.class_map.items()
            for cname, nid in classes.items()
            if cname == name
        ]
        return hits[0] if len(hits) == 1 else None

    def _global_class_node_lookup(self, name: str, idx: "_Index"):
        for fp, classes in idx.class_node_map.items():
            node = classes.get(name)
            if node:
                return node
        return None


# ── Index data structure ──────────────────────────────────────────────────────


class _Index:
    """In-memory indexes built during Phase 1."""

    def __init__(self):
        # path → file_node_id
        self.file_map: Dict[str, str] = {}
        # path → {symbol_name: node_id}  (functions, methods, classes)
        self.symbol_map: Dict[str, Dict[str, str]] = defaultdict(dict)
        # symbol_name → [(path, node_id), …]  for global uniqueness checks
        self.global_symbol_map: Dict[str, List[tuple]] = defaultdict(list)
        # path → {class_name: class_node_id}
        self.class_map: Dict[str, Dict[str, str]] = defaultdict(dict)
        # path → {class_name: SayouNode}  (full node, needed for override detection)
        self.class_node_map: Dict[str, Dict] = defaultdict(dict)
        # path → {class_name → {method_name: method_node_id}}
        self.method_map: Dict[str, Dict[str, Dict[str, str]]] = defaultdict(
            lambda: defaultdict(dict)
        )


# ── helpers ───────────────────────────────────────────────────────────────────


def _norm(path: str) -> str:
    return path.replace("\\", "/") if path else ""


def _no_ext(path: str) -> str:
    return os.path.splitext(path)[0]


def _edge(
    src: str,
    tgt: str,
    pred: str,
    confidence: str,
    resolution: str,
    source: str,
) -> Dict[str, Any]:
    return {
        "source": src,
        "target": tgt,
        "type": pred,
        SayouEdgeMeta.CONFIDENCE: confidence,
        SayouEdgeMeta.RESOLUTION: resolution,
        SayouEdgeMeta.EDGE_SOURCE: source,
    }
