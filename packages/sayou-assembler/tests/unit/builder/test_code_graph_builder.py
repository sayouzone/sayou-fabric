"""
Unit tests for CodeGraphBuilder.

Each test exercises one edge type in isolation using minimal hand-crafted
SayouNode fixtures.  Every assertion is named after the predicate it tests.

Edge types covered
──────────────────
CONTAINS      — FILE → CLASS/FUNC/METHOD/BLOCK
IMPORTS       — BLOCK → FILE/SYMBOL  (relative + absolute)
CALLS         — FUNC/METHOD → FUNC/METHOD  (same-file, same-class, global-unique)
MAYBE_CALLS   — FUNC/METHOD → FUNC/METHOD  (unambiguous attr call)
INHERITS      — CLASS → CLASS  (same-file + global lookup)
OVERRIDES     — METHOD → METHOD  (child redefines parent method)
USES_TYPE     — FUNC/METHOD → CLASS  (annotation / isinstance)
MUTATES_GLOBAL— FUNC/METHOD → CODE_BLOCK  (global x declaration)
RAISES        — FUNC/METHOD → virtual exc node  (sayou:exc:<Name>)
EXPOSES       — FILE → FUNC/CLASS  (__all__ declaration)
Node-rel merge— Pass-1 CONTAINS / HAS_PARENT relationships → edges
"""

import logging
import pytest
from sayou.assembler.plugins.code_graph_builder import CodeGraphBuilder
from sayou.core.schemas import SayouNode, SayouOutput
from sayou.core.ontology import (
    SayouClass,
    SayouAttribute,
    SayouPredicate,
    SayouEdgeMeta,
)

FILE_PATH = "sayou/refinery/pipeline.py"
FILE_PATH2 = "sayou/refinery/helpers.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _builder() -> CodeGraphBuilder:
    b = CodeGraphBuilder()
    b.logger = logging.getLogger("test")
    b._callbacks = []
    return b


def _file(path=FILE_PATH, **attrs):
    return SayouNode(
        node_id=f"sayou:file:{path.replace('/', '_')}",
        node_class=SayouClass.FILE,
        attributes={SayouAttribute.FILE_PATH: path, **attrs},
    )


def _class(name, path=FILE_PATH, **attrs):
    return SayouNode(
        node_id=f"sayou:class:{path.replace('/', '_')}::{name}",
        node_class=SayouClass.CLASS,
        attributes={
            SayouAttribute.FILE_PATH: path,
            SayouAttribute.SYMBOL_NAME: name,
            **attrs,
        },
    )


def _method(name, parent, path=FILE_PATH, **attrs):
    return SayouNode(
        node_id=f"sayou:method:{path.replace('/', '_')}::{parent}.{name}",
        node_class=SayouClass.METHOD,
        attributes={
            SayouAttribute.FILE_PATH: path,
            SayouAttribute.SYMBOL_NAME: name,
            SayouAttribute.PARENT_CLASS: parent,
            **attrs,
        },
    )


def _func(name, path=FILE_PATH, **attrs):
    return SayouNode(
        node_id=f"sayou:func:{path.replace('/', '_')}::{name}",
        node_class=SayouClass.FUNCTION,
        attributes={
            SayouAttribute.FILE_PATH: path,
            SayouAttribute.SYMBOL_NAME: name,
            **attrs,
        },
    )


def _block(idx=0, path=FILE_PATH, **attrs):
    return SayouNode(
        node_id=f"sayou:block:{path.replace('/', '_')}::{idx}",
        node_class=SayouClass.CODE_BLOCK,
        attributes={SayouAttribute.FILE_PATH: path, **attrs},
    )


def _output(*nodes):
    return SayouOutput(nodes=list(nodes))


def _edges_of(result, pred):
    return [e for e in result["edges"] if e["type"] == pred]


def _build(b, *nodes, **kwargs):
    return b._do_build(_output(*nodes), **kwargs)


# ---------------------------------------------------------------------------
# CONTAINS
# ---------------------------------------------------------------------------


class TestEdgeContains:
    def test_file_contains_class(self):
        b = _builder()
        f = _file()
        c = _class("MyClass")
        result = _build(b, f, c)
        edges = _edges_of(result, SayouPredicate.CONTAINS)
        assert any(e["source"] == f.node_id and e["target"] == c.node_id for e in edges)

    def test_file_contains_function(self):
        b = _builder()
        f = _file()
        fn = _func("parse")
        result = _build(b, f, fn)
        edges = _edges_of(result, SayouPredicate.CONTAINS)
        assert any(
            e["source"] == f.node_id and e["target"] == fn.node_id for e in edges
        )

    def test_file_contains_code_block(self):
        b = _builder()
        f = _file()
        blk = _block(0)
        result = _build(b, f, blk)
        edges = _edges_of(result, SayouPredicate.CONTAINS)
        assert any(
            e["source"] == f.node_id and e["target"] == blk.node_id for e in edges
        )

    def test_file_node_not_contained_by_itself(self):
        b = _builder()
        f = _file()
        result = _build(b, f)
        edges = _edges_of(result, SayouPredicate.CONTAINS)
        assert not any(
            e["source"] == f.node_id and e["target"] == f.node_id for e in edges
        )

    def test_node_without_file_path_skipped(self):
        b = _builder()
        orphan = SayouNode(
            node_id="orphan", node_class=SayouClass.FUNCTION, attributes={}
        )
        result = _build(b, orphan)
        edges = _edges_of(result, SayouPredicate.CONTAINS)
        assert all(e["target"] != "orphan" for e in edges)


# ---------------------------------------------------------------------------
# CALLS
# ---------------------------------------------------------------------------


class TestEdgeCalls:
    def test_function_calls_same_file_function(self):
        b = _builder()
        caller = _func("runner", **{SayouAttribute.CALLS_RAW: ["helper"]})
        callee = _func("helper")
        result = _build(b, caller, callee)
        edges = _edges_of(result, SayouPredicate.CALLS)
        assert any(
            e["source"] == caller.node_id and e["target"] == callee.node_id
            for e in edges
        )

    def test_method_calls_sibling_method(self):
        b = _builder()
        caller = _method("run", "MyClass", **{SayouAttribute.CALLS_RAW: ["_validate"]})
        callee = _method("_validate", "MyClass")
        result = _build(b, caller, callee)
        edges = _edges_of(result, SayouPredicate.CALLS)
        assert any(
            e["source"] == caller.node_id and e["target"] == callee.node_id
            for e in edges
        )

    def test_calls_global_unique_symbol(self):
        b = _builder()
        caller = _func("main", **{SayouAttribute.CALLS_RAW: ["load"]})
        callee = _func("load", path=FILE_PATH2)
        result = _build(b, caller, callee)
        edges = _edges_of(result, SayouPredicate.CALLS)
        assert any(
            e["source"] == caller.node_id and e["target"] == callee.node_id
            for e in edges
        )

    def test_calls_confidence_high(self):
        b = _builder()
        caller = _func("a", **{SayouAttribute.CALLS_RAW: ["b"]})
        callee = _func("b")
        result = _build(b, caller, callee)
        edges = _edges_of(result, SayouPredicate.CALLS)
        assert all(e[SayouEdgeMeta.CONFIDENCE] == "HIGH" for e in edges)

    def test_self_call_not_emitted(self):
        b = _builder()
        fn = _func("recurse", **{SayouAttribute.CALLS_RAW: ["recurse"]})
        result = _build(b, fn)
        edges = _edges_of(result, SayouPredicate.CALLS)
        assert not any(e["source"] == e["target"] for e in edges)

    def test_unresolved_call_produces_no_edge(self):
        b = _builder()
        fn = _func("runner", **{SayouAttribute.CALLS_RAW: ["unknown_fn"]})
        result = _build(b, fn)
        assert len(_edges_of(result, SayouPredicate.CALLS)) == 0

    def test_async_mismatch_flagged(self):
        """Sync caller → async callee should set async_mismatch=True."""
        b = _builder()
        caller = _func(
            "sync_fn",
            **{SayouAttribute.CALLS_RAW: ["async_fn"], SayouAttribute.IS_ASYNC: False},
        )
        callee = _func("async_fn", **{SayouAttribute.IS_ASYNC: True})
        result = _build(b, caller, callee)
        call_edges = _edges_of(result, SayouPredicate.CALLS)
        assert any(e.get("async_mismatch") is True for e in call_edges)


# ---------------------------------------------------------------------------
# MAYBE_CALLS
# ---------------------------------------------------------------------------


class TestEdgeMaybeCalls:
    def test_unambiguous_attr_call_produces_edge(self):
        b = _builder()
        caller = _func("go", **{SayouAttribute.ATTR_CALLS_RAW: ["process"]})
        callee = _func("process", path=FILE_PATH2)
        result = _build(b, caller, callee)
        edges = _edges_of(result, SayouPredicate.MAYBE_CALLS)
        assert len(edges) == 1
        assert edges[0][SayouEdgeMeta.CONFIDENCE] == "LOW"

    def test_ambiguous_attr_call_produces_no_edge(self):
        """Two symbols with the same name → ambiguous → skip."""
        b = _builder()
        caller = _func("go", **{SayouAttribute.ATTR_CALLS_RAW: ["save"]})
        callee1 = _func("save", path=FILE_PATH)
        callee2 = _func("save", path=FILE_PATH2)
        result = _build(b, caller, callee1, callee2)
        assert len(_edges_of(result, SayouPredicate.MAYBE_CALLS)) == 0

    def test_property_method_skipped(self):
        """@property methods are reads, not calls → no MAYBE_CALLS edge."""
        b = _builder()
        caller = _func("go", **{SayouAttribute.ATTR_CALLS_RAW: ["value"]})
        prop = _func(
            "value", path=FILE_PATH2, **{SayouAttribute.DECORATORS_RAW: ["property"]}
        )
        result = _build(b, caller, prop)
        assert len(_edges_of(result, SayouPredicate.MAYBE_CALLS)) == 0


# ---------------------------------------------------------------------------
# INHERITS
# ---------------------------------------------------------------------------


class TestEdgeInherits:
    def test_class_inherits_same_file_base(self):
        b = _builder()
        child = _class("Child", **{SayouAttribute.INHERITS_FROM_RAW: ["Base"]})
        parent = _class("Base")
        result = _build(b, child, parent)
        edges = _edges_of(result, SayouPredicate.INHERITS)
        assert any(
            e["source"] == child.node_id and e["target"] == parent.node_id
            for e in edges
        )

    def test_class_inherits_global_unique_base(self):
        b = _builder()
        child = _class(
            "Child",
            path=FILE_PATH,
            **{SayouAttribute.INHERITS_FROM_RAW: ["BaseComponent"]},
        )
        parent = _class("BaseComponent", path=FILE_PATH2)
        result = _build(b, child, parent)
        edges = _edges_of(result, SayouPredicate.INHERITS)
        assert len(edges) == 1

    def test_unresolved_base_produces_no_edge(self):
        b = _builder()
        child = _class("Child", **{SayouAttribute.INHERITS_FROM_RAW: ["Unknown"]})
        result = _build(b, child)
        assert len(_edges_of(result, SayouPredicate.INHERITS)) == 0


# ---------------------------------------------------------------------------
# OVERRIDES
# ---------------------------------------------------------------------------


class TestEdgeOverrides:
    def test_child_method_overrides_parent_method(self):
        b = _builder()
        parent_cls = _class("Base", path=FILE_PATH2)
        parent_method = _method("run", "Base", path=FILE_PATH2)
        child_cls = _class(
            "Child", path=FILE_PATH, **{SayouAttribute.INHERITS_FROM_RAW: ["Base"]}
        )
        child_method = _method("run", "Child", path=FILE_PATH)
        result = _build(b, parent_cls, parent_method, child_cls, child_method)
        edges = _edges_of(result, SayouPredicate.OVERRIDES)
        assert any(
            e["source"] == child_method.node_id and e["target"] == parent_method.node_id
            for e in edges
        )

    def test_abstract_parent_flagged(self):
        b = _builder()
        parent_cls = _class("Base", path=FILE_PATH2)
        parent_method = _method(
            "execute",
            "Base",
            path=FILE_PATH2,
            **{SayouAttribute.DECORATORS_RAW: ["abstractmethod"]},
        )
        child_cls = _class(
            "Child", path=FILE_PATH, **{SayouAttribute.INHERITS_FROM_RAW: ["Base"]}
        )
        child_method = _method("execute", "Child", path=FILE_PATH)
        result = _build(b, parent_cls, parent_method, child_cls, child_method)
        edges = _edges_of(result, SayouPredicate.OVERRIDES)
        assert any(e.get("abstract_parent") is True for e in edges)

    def test_unique_method_name_not_overrides(self):
        b = _builder()
        parent_cls = _class("Base", path=FILE_PATH2)
        parent_method = _method("run", "Base", path=FILE_PATH2)
        child_cls = _class(
            "Child", path=FILE_PATH, **{SayouAttribute.INHERITS_FROM_RAW: ["Base"]}
        )
        child_method = _method("stop", "Child", path=FILE_PATH)
        result = _build(b, parent_cls, parent_method, child_cls, child_method)
        assert len(_edges_of(result, SayouPredicate.OVERRIDES)) == 0


# ---------------------------------------------------------------------------
# USES_TYPE
# ---------------------------------------------------------------------------


class TestEdgeUsesType:
    def test_function_uses_type_same_file(self):
        b = _builder()
        fn = _func("process", **{SayouAttribute.TYPE_REFS_RAW: ["Config"]})
        cls = _class("Config")
        result = _build(b, fn, cls)
        edges = _edges_of(result, SayouPredicate.USES_TYPE)
        assert any(
            e["source"] == fn.node_id and e["target"] == cls.node_id for e in edges
        )

    def test_uses_type_confidence_medium(self):
        b = _builder()
        fn = _func("f", **{SayouAttribute.TYPE_REFS_RAW: ["Config"]})
        cls = _class("Config")
        result = _build(b, fn, cls)
        edges = _edges_of(result, SayouPredicate.USES_TYPE)
        assert all(e[SayouEdgeMeta.CONFIDENCE] == "MEDIUM" for e in edges)

    def test_non_function_node_skipped(self):
        b = _builder()
        cls1 = _class("A", **{SayouAttribute.TYPE_REFS_RAW: ["B"]})
        cls2 = _class("B")
        result = _build(b, cls1, cls2)
        assert len(_edges_of(result, SayouPredicate.USES_TYPE)) == 0


# ---------------------------------------------------------------------------
# MUTATES_GLOBAL
# ---------------------------------------------------------------------------


class TestEdgeMutatesGlobal:
    def test_function_mutates_global_var(self):
        b = _builder()
        blk = _block(0, **{SayouAttribute.MODULE_VARS_RAW: ["REGISTRY"]})
        fn = _func("register", **{SayouAttribute.GLOBALS_DECLARED_RAW: ["REGISTRY"]})
        result = _build(b, blk, fn)
        edges = _edges_of(result, SayouPredicate.MUTATES_GLOBAL)
        assert any(
            e["source"] == fn.node_id and e["target"] == blk.node_id for e in edges
        )

    def test_unresolved_global_produces_no_edge(self):
        b = _builder()
        fn = _func("mutate", **{SayouAttribute.GLOBALS_DECLARED_RAW: ["MISSING_VAR"]})
        result = _build(b, fn)
        assert len(_edges_of(result, SayouPredicate.MUTATES_GLOBAL)) == 0


# ---------------------------------------------------------------------------
# RAISES
# ---------------------------------------------------------------------------


class TestEdgeRaises:
    def test_function_raises_exception(self):
        b = _builder()
        fn = _func("parse", **{SayouAttribute.RAISES_RAW: ["ValueError"]})
        result = _build(b, fn)
        edges = _edges_of(result, SayouPredicate.RAISES)
        assert len(edges) == 1
        assert edges[0]["target"] == "sayou:exc:ValueError"

    def test_multiple_exceptions(self):
        b = _builder()
        fn = _func("validate", **{SayouAttribute.RAISES_RAW: ["TypeError", "KeyError"]})
        result = _build(b, fn)
        targets = {e["target"] for e in _edges_of(result, SayouPredicate.RAISES)}
        assert targets == {"sayou:exc:TypeError", "sayou:exc:KeyError"}

    def test_raises_confidence_high(self):
        b = _builder()
        fn = _func("f", **{SayouAttribute.RAISES_RAW: ["RuntimeError"]})
        result = _build(b, fn)
        edges = _edges_of(result, SayouPredicate.RAISES)
        assert all(e[SayouEdgeMeta.CONFIDENCE] == "HIGH" for e in edges)

    def test_non_function_does_not_raise_edges(self):
        b = _builder()
        cls = _class("MyClass", **{SayouAttribute.RAISES_RAW: ["ValueError"]})
        result = _build(b, cls)
        assert len(_edges_of(result, SayouPredicate.RAISES)) == 0


# ---------------------------------------------------------------------------
# EXPOSES (__all__)
# ---------------------------------------------------------------------------


class TestEdgeExposes:
    def test_file_exposes_function_in_all(self):
        b = _builder()
        f = _file(**{SayouAttribute.MODULE_ALL_RAW: ["public_fn"]})
        fn = _func("public_fn")
        result = _build(b, f, fn)
        edges = _edges_of(result, SayouPredicate.EXPOSES)
        assert any(
            e["source"] == f.node_id and e["target"] == fn.node_id for e in edges
        )

    def test_file_exposes_class_in_all(self):
        b = _builder()
        f = _file(**{SayouAttribute.MODULE_ALL_RAW: ["PublicClass"]})
        cls = _class("PublicClass")
        result = _build(b, f, cls)
        edges = _edges_of(result, SayouPredicate.EXPOSES)
        assert any(
            e["source"] == f.node_id and e["target"] == cls.node_id for e in edges
        )

    def test_symbol_not_in_all_not_exposed(self):
        b = _builder()
        f = _file(**{SayouAttribute.MODULE_ALL_RAW: ["public_fn"]})
        fn = _func("internal_fn")  # not in __all__
        result = _build(b, f, fn)
        edges = _edges_of(result, SayouPredicate.EXPOSES)
        assert all(e["target"] != fn.node_id for e in edges)


# ---------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------


class TestEdgeImports:
    def test_relative_import_resolved(self):
        b = _builder()
        src_path = "sayou/refinery/pipeline.py"
        tgt_path = "sayou/refinery/helpers.py"

        importer = _block(
            0,
            path=src_path,
            **{"sayou:importsRaw": [{"module": "helpers", "name": None, "level": 1}]},
        )
        target_file = _file(tgt_path)
        result = _build(b, importer, target_file)
        edges = _edges_of(result, SayouPredicate.IMPORTS)
        assert any(
            e["source"] == importer.node_id and e["target"] == target_file.node_id
            for e in edges
        )


# ---------------------------------------------------------------------------
# Node-relationship merge
# ---------------------------------------------------------------------------


class TestNodeRelMerge:
    def test_pass1_contains_relationships_become_edges(self):
        """
        CONTAINS relationships set on nodes in Pass-1 (e.g. by CodeChunkAdapter)
        must be merged into the edge list.
        """
        b = _builder()
        cls = _class("MyClass")
        method = _method(
            "run",
            "MyClass",
            relationships={SayouPredicate.CONTAINS: ["sayou:method::MyClass.run"]},
        )
        # Inject relationships directly
        cls.relationships[SayouPredicate.CONTAINS] = [method.node_id]
        result = _build(b, cls, method)
        contains_edges = _edges_of(result, SayouPredicate.CONTAINS)
        assert any(
            e["source"] == cls.node_id and e["target"] == method.node_id
            for e in contains_edges
        )


# ---------------------------------------------------------------------------
# can_handle
# ---------------------------------------------------------------------------


class TestCanHandle:
    def test_code_graph_strategy(self):
        assert CodeGraphBuilder.can_handle(_output(), "code_graph") == 1.0

    def test_code_structure_strategy(self):
        assert CodeGraphBuilder.can_handle(_output(), "code_structure") == 1.0

    def test_non_empty_output_auto(self):
        fn = _func("f")
        assert CodeGraphBuilder.can_handle(_output(fn), "auto") == 1.0

    def test_empty_output_auto_returns_zero(self):
        assert CodeGraphBuilder.can_handle(_output(), "auto") == 0.0
