"""
Unit tests for CodeChunkAdapter.

Covers:
- can_handle(): strategy key, metadata heuristics, empty list
- _do_adapt():
  - File node creation (one per source, deduplication)
  - class_header  → SayouClass.CLASS  (Pass-1 class_nodes dict)
  - method        → SayouClass.METHOD + HAS_PARENT + CONTAINS (Pass-2)
  - function      → SayouClass.FUNCTION
  - class_attrs   → SayouClass.ATTRIBUTE_BLOCK + CONTAINS (Pass-2)
  - code_block    → SayouClass.CODE_BLOCK
  - call-graph raw attributes forwarded
  - stable symbol-based node IDs
  - output metadata source field
"""

import pytest
from sayou.core.ontology import SayouAttribute, SayouClass, SayouPredicate
from sayou.core.schemas import SayouChunk, SayouOutput

from sayou.wrapper.plugins.code_chunk_adapter import CodeChunkAdapter

SOURCE = "sayou/refinery/pipeline.py"


def _chunk(sem_type, content="code", **meta):
    base = {
        "semantic_type": sem_type,
        "source": SOURCE,
        "language": "python",
        "chunk_index": 0,
        "lineStart": 1,
        "lineEnd": 2,
    }
    base.update(meta)
    return SayouChunk(content=content, metadata=base)


def _adapter():
    import logging

    a = CodeChunkAdapter()
    a.logger = logging.getLogger("test")
    a._callbacks = []
    a.config = {}
    return a


def _by_class(output, cls):
    return [n for n in output.nodes if n.node_class == cls]


# ---------------------------------------------------------------------------
# can_handle
# ---------------------------------------------------------------------------


class TestCanHandle:
    def test_explicit_strategy_returns_1(self):
        assert CodeChunkAdapter.can_handle([], "code_chunk") == 1.0

    def test_source_metadata_scores_high(self):
        chunks = [SayouChunk(content="x", metadata={"source": "main.py"})]
        assert CodeChunkAdapter.can_handle(chunks, "auto") >= 0.9

    def test_extension_metadata_scores_high(self):
        chunks = [
            SayouChunk(content="x", metadata={"extension": ".py", "source": "f.py"})
        ]
        assert CodeChunkAdapter.can_handle(chunks, "auto") >= 0.9

    def test_empty_list_returns_zero(self):
        assert CodeChunkAdapter.can_handle([], "auto") == 0.0

    def test_non_list_returns_zero(self):
        assert CodeChunkAdapter.can_handle("plain string", "auto") == 0.0


# ---------------------------------------------------------------------------
# File node
# ---------------------------------------------------------------------------


class TestFileNode:
    def test_one_file_node_per_source(self):
        a = _adapter()
        output = a._do_adapt([_chunk("code_block")])
        assert len(_by_class(output, SayouClass.FILE)) == 1

    def test_file_node_deduplication(self):
        a = _adapter()
        chunks = [_chunk("code_block", chunk_index=i) for i in range(4)]
        output = a._do_adapt(chunks)
        assert len(_by_class(output, SayouClass.FILE)) == 1

    def test_file_node_carries_path_and_language(self):
        a = _adapter()
        output = a._do_adapt([_chunk("code_block")])
        fn = _by_class(output, SayouClass.FILE)[0]
        assert fn.attributes.get(SayouAttribute.FILE_PATH) == SOURCE
        assert fn.attributes.get(SayouAttribute.LANGUAGE) == "python"

    def test_two_sources_produce_two_file_nodes(self):
        a = _adapter()
        c1 = SayouChunk(
            content="x",
            metadata={
                "semantic_type": "code_block",
                "source": "a.py",
                "language": "python",
                "chunk_index": 0,
            },
        )
        c2 = SayouChunk(
            content="y",
            metadata={
                "semantic_type": "code_block",
                "source": "b.py",
                "language": "python",
                "chunk_index": 0,
            },
        )
        output = a._do_adapt([c1, c2])
        assert len(_by_class(output, SayouClass.FILE)) == 2


# ---------------------------------------------------------------------------
# class_header
# ---------------------------------------------------------------------------


class TestClassHeader:
    def test_class_node_created(self):
        a = _adapter()
        output = a._do_adapt([_chunk("class_header", class_name="MyClass")])
        assert len(_by_class(output, SayouClass.CLASS)) == 1

    def test_class_node_id_contains_symbol(self):
        a = _adapter()
        output = a._do_adapt([_chunk("class_header", class_name="Pipeline")])
        node = _by_class(output, SayouClass.CLASS)[0]
        assert "Pipeline" in node.node_id

    def test_class_friendly_name(self):
        a = _adapter()
        output = a._do_adapt([_chunk("class_header", class_name="MyClass")])
        node = _by_class(output, SayouClass.CLASS)[0]
        assert node.friendly_name == "MyClass"

    def test_inherits_from_raw_forwarded(self):
        a = _adapter()
        output = a._do_adapt(
            [
                _chunk(
                    "class_header", class_name="Child", inherits_from=["BaseComponent"]
                )
            ]
        )
        node = _by_class(output, SayouClass.CLASS)[0]
        assert node.attributes.get(SayouAttribute.INHERITS_FROM_RAW) == [
            "BaseComponent"
        ]

    def test_class_has_defined_in_relationship(self):
        a = _adapter()
        output = a._do_adapt([_chunk("class_header", class_name="MyClass")])
        node = _by_class(output, SayouClass.CLASS)[0]
        assert SayouPredicate.DEFINED_IN in node.relationships


# ---------------------------------------------------------------------------
# method
# ---------------------------------------------------------------------------


class TestMethod:
    def test_method_node_created(self):
        a = _adapter()
        output = a._do_adapt(
            [
                _chunk("class_header", class_name="MyClass"),
                _chunk("method", parent_node="MyClass", function_name="run"),
            ]
        )
        assert len(_by_class(output, SayouClass.METHOD)) == 1

    def test_method_node_id_contains_class_and_method(self):
        a = _adapter()
        output = a._do_adapt(
            [
                _chunk("class_header", class_name="MyClass"),
                _chunk("method", parent_node="MyClass", function_name="execute"),
            ]
        )
        node = _by_class(output, SayouClass.METHOD)[0]
        assert "MyClass" in node.node_id
        assert "execute" in node.node_id

    def test_method_has_parent_relationship(self):
        a = _adapter()
        output = a._do_adapt(
            [
                _chunk("class_header", class_name="MyClass"),
                _chunk("method", parent_node="MyClass", function_name="run"),
            ]
        )
        method = _by_class(output, SayouClass.METHOD)[0]
        assert SayouPredicate.HAS_PARENT in method.relationships

    def test_class_contains_method_after_pass2(self):
        """Pass 2 should inject CONTAINS edges into the class node."""
        a = _adapter()
        output = a._do_adapt(
            [
                _chunk("class_header", class_name="MyClass"),
                _chunk("method", parent_node="MyClass", function_name="run"),
                _chunk("method", parent_node="MyClass", function_name="stop"),
            ]
        )
        cls_node = _by_class(output, SayouClass.CLASS)[0]
        contains = cls_node.relationships.get(SayouPredicate.CONTAINS, [])
        assert len(contains) == 2

    def test_calls_raw_forwarded(self):
        a = _adapter()
        output = a._do_adapt(
            [
                _chunk("class_header", class_name="C"),
                _chunk(
                    "method",
                    parent_node="C",
                    function_name="run",
                    calls=["helper", "logger"],
                ),
            ]
        )
        method = _by_class(output, SayouClass.METHOD)[0]
        assert method.attributes.get(SayouAttribute.CALLS_RAW) == ["helper", "logger"]

    def test_is_async_forwarded(self):
        a = _adapter()
        output = a._do_adapt(
            [
                _chunk("class_header", class_name="C"),
                _chunk("method", parent_node="C", function_name="fetch", is_async=True),
            ]
        )
        method = _by_class(output, SayouClass.METHOD)[0]
        assert method.attributes.get(SayouAttribute.IS_ASYNC) is True


# ---------------------------------------------------------------------------
# function (top-level)
# ---------------------------------------------------------------------------


class TestFunction:
    def test_function_node_created(self):
        a = _adapter()
        output = a._do_adapt([_chunk("function", function_name="parse_config")])
        assert len(_by_class(output, SayouClass.FUNCTION)) == 1

    def test_function_node_id_contains_name(self):
        a = _adapter()
        output = a._do_adapt([_chunk("function", function_name="load_data")])
        node = _by_class(output, SayouClass.FUNCTION)[0]
        assert "load_data" in node.node_id

    def test_function_not_inside_class_contains(self):
        """Top-level functions must NOT appear in any class CONTAINS list."""
        a = _adapter()
        output = a._do_adapt(
            [
                _chunk("class_header", class_name="MyClass"),
                _chunk("function", function_name="standalone"),
            ]
        )
        cls_node = _by_class(output, SayouClass.CLASS)[0]
        contains = cls_node.relationships.get(SayouPredicate.CONTAINS, [])
        func = _by_class(output, SayouClass.FUNCTION)[0]
        assert func.node_id not in contains

    def test_type_refs_raw_forwarded(self):
        a = _adapter()
        output = a._do_adapt(
            [
                _chunk(
                    "function",
                    function_name="process",
                    type_refs=["SayouBlock", "SayouChunk"],
                )
            ]
        )
        node = _by_class(output, SayouClass.FUNCTION)[0]
        assert node.attributes.get(SayouAttribute.TYPE_REFS_RAW) == [
            "SayouBlock",
            "SayouChunk",
        ]


# ---------------------------------------------------------------------------
# class_attributes
# ---------------------------------------------------------------------------


class TestClassAttributes:
    def test_attribute_block_created(self):
        a = _adapter()
        output = a._do_adapt(
            [
                _chunk("class_header", class_name="MyClass"),
                _chunk("class_attributes", parent_node="MyClass"),
            ]
        )
        assert len(_by_class(output, SayouClass.ATTRIBUTE_BLOCK)) == 1

    def test_attribute_block_in_class_contains(self):
        a = _adapter()
        output = a._do_adapt(
            [
                _chunk("class_header", class_name="MyClass"),
                _chunk("class_attributes", parent_node="MyClass"),
            ]
        )
        cls_node = _by_class(output, SayouClass.CLASS)[0]
        contains = cls_node.relationships.get(SayouPredicate.CONTAINS, [])
        attrs_node = _by_class(output, SayouClass.ATTRIBUTE_BLOCK)[0]
        assert attrs_node.node_id in contains

    def test_attribute_block_has_parent(self):
        a = _adapter()
        output = a._do_adapt(
            [
                _chunk("class_header", class_name="MyClass"),
                _chunk("class_attributes", parent_node="MyClass"),
            ]
        )
        attrs_node = _by_class(output, SayouClass.ATTRIBUTE_BLOCK)[0]
        assert SayouPredicate.HAS_PARENT in attrs_node.relationships


# ---------------------------------------------------------------------------
# generic code_block
# ---------------------------------------------------------------------------


class TestCodeBlock:
    def test_code_block_created_for_unknown_sem_type(self):
        a = _adapter()
        output = a._do_adapt([_chunk("imports", content="import os")])
        assert len(_by_class(output, SayouClass.CODE_BLOCK)) == 1

    def test_code_block_id_contains_index(self):
        a = _adapter()
        output = a._do_adapt([_chunk("code_block", chunk_index=7)])
        node = _by_class(output, SayouClass.CODE_BLOCK)[0]
        assert "7" in node.node_id

    def test_module_vars_raw_forwarded(self):
        a = _adapter()
        output = a._do_adapt([_chunk("code_block", module_vars=["REGISTRY", "LOGGER"])])
        node = _by_class(output, SayouClass.CODE_BLOCK)[0]
        assert node.attributes.get(SayouAttribute.MODULE_VARS_RAW) == [
            "REGISTRY",
            "LOGGER",
        ]


# ---------------------------------------------------------------------------
# Full pipeline (integration-style unit test)
# ---------------------------------------------------------------------------


class TestFullPipeline:
    def test_realistic_module_structure(self):
        """
        File with: 1 import block + 1 class (2 methods + attrs) + 1 function.
        Expected node counts:
          File=1, Class=1, Method=2, AttributeBlock=1, Function=1, CodeBlock=1
        """
        a = _adapter()
        chunks = [
            _chunk("code_block", content="import os", chunk_index=0),
            _chunk("class_header", class_name="Parser"),
            _chunk("class_attributes", parent_node="Parser"),
            _chunk("method", parent_node="Parser", function_name="parse"),
            _chunk("method", parent_node="Parser", function_name="_validate"),
            _chunk("function", function_name="load_config"),
        ]
        output = a._do_adapt(chunks)

        assert len(_by_class(output, SayouClass.FILE)) == 1
        assert len(_by_class(output, SayouClass.CLASS)) == 1
        assert len(_by_class(output, SayouClass.METHOD)) == 2
        assert len(_by_class(output, SayouClass.ATTRIBUTE_BLOCK)) == 1
        assert len(_by_class(output, SayouClass.FUNCTION)) == 1
        assert len(_by_class(output, SayouClass.CODE_BLOCK)) == 1

    def test_output_metadata_source(self):
        a = _adapter()
        output = a._do_adapt([_chunk("code_block")])
        assert output.metadata.get("source") == "sayou-code-adapter"
