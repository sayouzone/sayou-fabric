"""
Integration tests for AssemblerPipeline end-to-end.
"""

import pytest
from sayou.core.ontology import SayouAttribute, SayouClass, SayouPredicate
from sayou.core.schemas import SayouNode, SayouOutput

from sayou.assembler.builder.graph_builder import GraphBuilder
from sayou.assembler.builder.vector_builder import VectorBuilder
from sayou.assembler.pipeline import AssemblerPipeline
from sayou.assembler.plugins.cypher_builder import CypherBuilder
from sayou.assembler.plugins.timeline_builder import TimelineBuilder


def _node(node_id, cls="Node", attrs=None, rels=None):
    return SayouNode(
        node_id=node_id,
        node_class=cls,
        attributes=attrs or {},
        relationships=rels or {},
    )


def _output(*nodes):
    return SayouOutput(nodes=list(nodes))


class TestGraphBuilderIntegration:
    def test_full_graph_pipeline(self):
        pipeline = AssemblerPipeline(extra_builders=[GraphBuilder])
        nodes = [
            _node("parent"),
            _node("child", rels={"sayou:hasParent": ["parent"]}),
        ]
        result = pipeline.run(_output(*nodes), strategy="GraphBuilder")
        assert "nodes" in result and "edges" in result
        assert len(result["nodes"]) == 2

    def test_reverse_edges_in_output(self):
        pipeline = AssemblerPipeline(extra_builders=[GraphBuilder])
        nodes = [_node("child", rels={"sayou:hasParent": ["parent"]})]
        result = pipeline.run(_output(*nodes), strategy="GraphBuilder")
        rev = [e for e in result["edges"] if e.get("is_reverse")]
        assert len(rev) >= 1

    def test_empty_output_returns_empty_list(self):
        pipeline = AssemblerPipeline(extra_builders=[GraphBuilder])
        result = pipeline.run([], strategy="GraphBuilder")
        assert result == []


class TestVectorBuilderIntegration:
    def test_vectors_attached_to_nodes(self):
        pipeline = AssemblerPipeline(extra_builders=[VectorBuilder])
        fn = lambda t: [0.5] * 4
        nodes = [
            _node("v1", attrs={"schema:text": "hello world"}),
            _node("v2", attrs={"schema:text": "goodbye world"}),
        ]
        result = pipeline.run(
            _output(*nodes), strategy="VectorBuilder", embedding_fn=fn
        )
        assert len(result) == 2
        assert result[0]["vector"] == [0.5, 0.5, 0.5, 0.5]

    def test_nodes_without_text_excluded(self):
        pipeline = AssemblerPipeline(extra_builders=[VectorBuilder])
        fn = lambda t: [1.0]
        nodes = [
            _node("has_text", attrs={"schema:text": "some text"}),
            _node("no_text", attrs={}),
        ]
        result = pipeline.run(
            _output(*nodes), strategy="VectorBuilder", embedding_fn=fn
        )
        assert len(result) == 1
        assert result[0]["id"] == "has_text"


class TestCypherBuilderIntegration:
    def test_cypher_queries_generated(self):
        pipeline = AssemblerPipeline(extra_builders=[CypherBuilder])
        nodes = [
            _node("n1", cls="Person", attrs={"name": "Alice"}),
            _node("n2", cls="Person", attrs={"name": "Bob"}, rels={"KNOWS": ["n1"]}),
        ]
        queries = pipeline.run(_output(*nodes), strategy="CypherBuilder")
        assert any("MERGE" in q for q in queries)
        assert any("MATCH" in q for q in queries)

    def test_relationship_query_references_both_nodes(self):
        pipeline = AssemblerPipeline(extra_builders=[CypherBuilder])
        nodes = [_node("src"), _node("tgt"), _node("src", rels={"REL": ["tgt"]})]
        queries = pipeline.run(_output(*nodes), strategy="CypherBuilder")
        rel_q = [q for q in queries if "MATCH" in q]
        assert any("src" in q and "tgt" in q for q in rel_q)


class TestTimelineBuilderIntegration:
    def _seg(self, node_id, start, parent):
        return SayouNode(
            node_id=node_id,
            node_class=SayouClass.VIDEO_SEGMENT,
            attributes={
                SayouAttribute.START_TIME: start,
                SayouAttribute.END_TIME: start + 2.0,
                "meta:parent_node": parent,
            },
        )

    def test_timeline_full_flow(self):
        pipeline = AssemblerPipeline(extra_builders=[TimelineBuilder])
        video = SayouNode(node_id="v1", node_class=SayouClass.VIDEO, attributes={})
        segs = [self._seg(f"s{i}", float(i * 3), "v1") for i in range(4)]
        result = pipeline.run(_output(video, *segs), strategy="TimelineBuilder")
        contains_edges = [
            e for e in result["edges"] if e["type"] == SayouPredicate.CONTAINS
        ]
        next_edges = [e for e in result["edges"] if e["type"] == SayouPredicate.NEXT]
        assert len(contains_edges) == 4  # one per segment
        assert len(next_edges) == 3  # 4 segments → 3 NEXT links
