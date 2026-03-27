"""
Unit tests for TimelineBuilder.
"""

import pytest
from sayou.core.ontology import SayouAttribute, SayouClass, SayouPredicate
from sayou.core.schemas import SayouNode, SayouOutput

from sayou.assembler.plugins.timeline_builder import TimelineBuilder


def _segment(node_id, start, parent):
    return SayouNode(
        node_id=node_id,
        node_class=SayouClass.VIDEO_SEGMENT,
        attributes={
            SayouAttribute.START_TIME: start,
            SayouAttribute.END_TIME: start + 2.0,
            "meta:parent_node": parent,
        },
    )


def _video(node_id):
    return SayouNode(node_id=node_id, node_class=SayouClass.VIDEO, attributes={})


def _output(*nodes):
    return SayouOutput(nodes=list(nodes))


class TestCanHandle:
    def test_output_with_video_segments_returns_1(self):
        s = _segment("s1", 0.0, "v1")
        assert TimelineBuilder.can_handle(_output(s)) == 1.0

    def test_output_without_segments_returns_zero(self):
        n = SayouNode(node_id="n1", node_class="Node", attributes={})
        assert TimelineBuilder.can_handle(_output(n)) == 0.0

    def test_dict_with_segment_nodes_returns_1(self):
        data = {"nodes": [{"node_class": SayouClass.VIDEO_SEGMENT}]}
        assert TimelineBuilder.can_handle(data) == 1.0


class TestDoBuild:
    def setup_method(self):
        import logging

        self.builder = TimelineBuilder()
        self.builder.logger = logging.getLogger("test")
        self.builder._callbacks = []

    def test_contains_edges_from_video_to_segments(self):
        segments = [_segment(f"s{i}", float(i), "v1") for i in range(3)]
        result = self.builder._do_build(_output(_video("v1"), *segments))
        contains = [e for e in result["edges"] if e["type"] == SayouPredicate.CONTAINS]
        assert len(contains) == 3
        assert all(e["source"] == "v1" for e in contains)

    def test_next_edges_link_segments_in_order(self):
        # Segments provided out-of-order; builder should sort by start_time
        s0 = _segment("s0", 0.0, "v1")
        s1 = _segment("s1", 5.0, "v1")
        s2 = _segment("s2", 2.5, "v1")  # out of order
        result = self.builder._do_build(_output(s0, s1, s2))
        next_edges = [e for e in result["edges"] if e["type"] == SayouPredicate.NEXT]
        assert len(next_edges) == 2
        # First NEXT edge: s0 → s2 (sorted by start_time)
        assert next_edges[0]["source"] == "s0"
        assert next_edges[0]["target"] == "s2"

    def test_last_segment_has_no_next_edge(self):
        segments = [_segment(f"s{i}", float(i), "v1") for i in range(3)]
        result = self.builder._do_build(_output(*segments))
        next_edges = [e for e in result["edges"] if e["type"] == SayouPredicate.NEXT]
        targets = {e["target"] for e in next_edges}
        # "s2" is the last segment; it should not appear as a source of NEXT
        sources = {e["source"] for e in next_edges}
        assert "s2" not in sources

    def test_nodes_preserved_in_output(self):
        s = _segment("s1", 0.0, "v1")
        result = self.builder._do_build(_output(_video("v1"), s))
        assert len(result["nodes"]) == 2

    def test_segments_without_parent_node_skipped(self):
        s_no_parent = SayouNode(
            node_id="s_orphan",
            node_class=SayouClass.VIDEO_SEGMENT,
            attributes={SayouAttribute.START_TIME: 0.0},  # no meta:parent_node
        )
        result = self.builder._do_build(_output(s_no_parent))
        assert result["edges"] == []
