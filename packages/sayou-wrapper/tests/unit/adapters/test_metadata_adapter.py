"""
Unit tests for MetadataAdapter.

Covers:
- can_handle(): explicit 'metadata' strategy, other strategies return 0
- _do_adapt():
  - metadata_map applied per node (callable per attribute key)
  - enrichment error isolation (one fn fails → others unaffected)
  - use_stub=True generates summary + keywords placeholders
  - empty content skips enrichment but still creates node
  - node_id taken from chunk_id / id in metadata
  - non-string content skips enrichment
"""

import pytest
from sayou.core.schemas import SayouOutput

from sayou.wrapper.plugins.metadata_adapter import MetadataAdapter


def _item(content="hello world", **meta):
    base = {"chunk_id": "c1"}
    base.update(meta)
    return {"content": content, "metadata": base}


def _adapter():
    import logging

    a = MetadataAdapter()
    a.logger = logging.getLogger("test")
    a._callbacks = []
    a.config = {}
    return a


# ---------------------------------------------------------------------------
# can_handle
# ---------------------------------------------------------------------------


class TestCanHandle:
    def test_metadata_strategy_returns_1(self):
        assert MetadataAdapter.can_handle([], "metadata") == 1.0

    def test_auto_strategy_returns_zero(self):
        assert MetadataAdapter.can_handle([], "auto") == 0.0

    def test_other_strategy_returns_zero(self):
        assert MetadataAdapter.can_handle([], "embedding") == 0.0


# ---------------------------------------------------------------------------
# metadata_map — enrichment functions applied
# ---------------------------------------------------------------------------


class TestMetadataMap:
    def test_single_function_applied(self):
        a = _adapter()
        output = a._do_adapt(
            [_item("hello world")],
            metadata_map={"word_count": lambda t: len(t.split())},
        )
        assert output.nodes[0].attributes.get("word_count") == 2

    def test_multiple_functions_all_applied(self):
        a = _adapter()
        output = a._do_adapt(
            [_item("foo bar baz")],
            metadata_map={
                "length": lambda t: len(t),
                "upper_first": lambda t: t[0].upper(),
            },
        )
        node = output.nodes[0]
        assert node.attributes.get("length") == 11
        assert node.attributes.get("upper_first") == "F"

    def test_function_applied_to_each_item(self):
        a = _adapter()
        items = [
            _item("one"),
            _item("two three", chunk_id="c2"),
            _item("four five six", chunk_id="c3"),
        ]
        output = a._do_adapt(
            items,
            metadata_map={"words": lambda t: len(t.split())},
        )
        counts = [n.attributes.get("words") for n in output.nodes]
        assert counts == [1, 2, 3]

    def test_non_callable_values_skipped(self):
        """Non-callable in metadata_map should not crash; just skip."""
        a = _adapter()
        output = a._do_adapt(
            [_item("test")],
            metadata_map={"bad_key": "not_a_function"},
        )
        # Should complete without error; bad_key not applied
        assert output.nodes[0].attributes.get("bad_key") is None

    def test_no_metadata_map_no_enrichment(self):
        a = _adapter()
        output = a._do_adapt([_item("test")])
        # No extra attributes beyond schema:text and metadata passthrough
        assert "word_count" not in output.nodes[0].attributes


# ---------------------------------------------------------------------------
# Error isolation
# ---------------------------------------------------------------------------


class TestEnrichmentErrorIsolation:
    def test_failing_fn_sets_attribute_to_none(self):
        a = _adapter()
        output = a._do_adapt(
            [_item("test")],
            metadata_map={
                "ok_attr": lambda t: "ok",
                "bad_attr": lambda t: 1 / 0,  # always raises
            },
        )
        node = output.nodes[0]
        assert node.attributes.get("ok_attr") == "ok"
        assert node.attributes.get("bad_attr") is None

    def test_error_in_one_item_does_not_affect_others(self):
        call_count = [0]

        def fragile(text):
            call_count[0] += 1
            if call_count[0] == 2:
                raise RuntimeError("intermittent failure")
            return "ok"

        a = _adapter()
        items = [_item("a"), _item("b", chunk_id="c2"), _item("c", chunk_id="c3")]
        output = a._do_adapt(items, metadata_map={"result": fragile})
        results = [n.attributes.get("result") for n in output.nodes]
        assert results[0] == "ok"
        assert results[1] is None  # failed
        assert results[2] == "ok"


# ---------------------------------------------------------------------------
# Stub mode
# ---------------------------------------------------------------------------


class TestStubMode:
    def test_stub_generates_summary_and_keywords(self):
        a = _adapter()
        output = a._do_adapt([_item("hello world")], use_stub=True)
        node = output.nodes[0]
        assert node.attributes.get("summary") is not None
        assert node.attributes.get("keywords") == ["stub", "test", "keyword"]

    def test_stub_summary_contains_content_prefix(self):
        a = _adapter()
        output = a._do_adapt([_item("sayou fabric test")], use_stub=True)
        summary = output.nodes[0].attributes.get("summary", "")
        assert "sayou fabric" in summary

    def test_stub_not_activated_when_metadata_map_present(self):
        """use_stub=True is ignored when metadata_map is supplied."""
        a = _adapter()
        output = a._do_adapt(
            [_item("test")],
            use_stub=True,
            metadata_map={"custom": lambda t: "custom_val"},
        )
        node = output.nodes[0]
        # metadata_map result present, stub placeholders absent
        assert node.attributes.get("custom") == "custom_val"
        assert node.attributes.get("summary") is None


# ---------------------------------------------------------------------------
# Node basics
# ---------------------------------------------------------------------------


class TestNodeBasics:
    def test_node_count_matches_input(self):
        a = _adapter()
        items = [_item("x", chunk_id=f"c{i}") for i in range(5)]
        output = a._do_adapt(items)
        assert len(output.nodes) == 5

    def test_node_id_from_chunk_id(self):
        a = _adapter()
        output = a._do_adapt([_item("x", chunk_id="my-chunk")])
        assert output.nodes[0].node_id == "my-chunk"

    def test_node_id_from_id_field(self):
        a = _adapter()
        output = a._do_adapt([{"content": "x", "metadata": {"id": "alt-id"}}])
        assert output.nodes[0].node_id == "alt-id"

    def test_empty_content_still_creates_node(self):
        a = _adapter()
        output = a._do_adapt([_item("", chunk_id="empty")])
        assert len(output.nodes) == 1

    def test_empty_content_skips_enrichment(self):
        a = _adapter()
        fn_called = []
        output = a._do_adapt(
            [_item("", chunk_id="empty")],
            metadata_map={"attr": lambda t: fn_called.append(t) or "val"},
        )
        assert fn_called == []  # fn not called for empty content

    def test_original_metadata_passthrough(self):
        a = _adapter()
        output = a._do_adapt([_item("x", custom_key="custom_val")])
        assert output.nodes[0].attributes.get("custom_key") == "custom_val"
