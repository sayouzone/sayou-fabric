from typing import Dict, List, Any
from dataclasses import dataclass, field

@dataclass
class GraphNode:
    id: str
    label: str
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GraphEdge:
    source: str
    target: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)

class KnowledgeGraph:
    """
    Assembler가 내부적으로 사용하는 인메모리 그래프 객체.
    """
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []

    def add_node(self, node: GraphNode):
        self.nodes[node.id] = node

    def add_edge(self, edge: GraphEdge):
        self.edges.append(edge)

    def to_dict(self) -> Dict[str, Any]:
        """JSON 직렬화를 위한 Dict 변환"""
        return {
            "nodes": [
                {"id": n.id, "label": n.label, "properties": n.properties}
                for n in self.nodes.values()
            ],
            "edges": [
                {"source": e.source, "target": e.target, "type": e.type, "properties": e.properties}
                for e in self.edges
            ],
            "summary": {
                "node_count": len(self.nodes),
                "edge_count": len(self.edges)
            }
        }