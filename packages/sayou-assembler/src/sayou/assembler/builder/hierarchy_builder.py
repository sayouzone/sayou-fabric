from typing import Dict, Any

from ..interfaces.base_builder import BaseBuilder
from ..graph.knowledge_graph import KnowledgeGraph, GraphNode, GraphEdge

class HierarchyBuilder(BaseBuilder):
    """
    (Tier 2) Wrapper의 표준 출력(Dict)을 받아 계층형 그래프로 조립합니다.
    """
    component_name = "HierarchyBuilder"
    SUPPORTED_TYPES = ['hierarchy']

    def build(self, wrapper_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Args:
            wrapper_output: sayou-wrapper의 실행 결과 (JSON Dict)
        """
        kg = KnowledgeGraph()
        
        # wrapper_output이 JSON 문자열로 들어왔을 경우를 대비한 방어 로직
        if isinstance(wrapper_output, str):
            import json
            wrapper_output = json.loads(wrapper_output)

        nodes_data = wrapper_output.get("nodes", [])
        
        # 1. 노드 생성
        for n_data in nodes_data:
            # Wrapper Schema: node_id, node_class, attributes, friendly_name
            node = GraphNode(
                id=n_data.get("node_id"),
                label=n_data.get("node_class", "Unknown"),
                properties={
                    "friendly_name": n_data.get("friendly_name"),
                    **n_data.get("attributes", {})
                }
            )
            kg.add_node(node)

        # 2. 엣지 생성 (정방향 & 역방향)
        for n_data in nodes_data:
            source_id = n_data.get("node_id")
            rels = n_data.get("relationships", {})
            
            for rel_type, targets in rels.items():
                if isinstance(targets, str): targets = [targets] # 방어 로직
                
                for target_id in targets:
                    if target_id not in kg.nodes:
                        continue # 대상 노드가 없으면 스킵

                    # 정방향
                    kg.add_edge(GraphEdge(source=source_id, target=target_id, type=rel_type))
                    
                    # 역방향
                    rev_type = self._get_reverse_type(rel_type)
                    kg.add_edge(GraphEdge(source=target_id, target=source_id, type=rev_type))

        # 객체가 아니라 Dict를 반환해야 파이프라인 호환성이 유지됨
        return kg.to_dict()

    def _get_reverse_type(self, rel_type: str) -> str:
        if "hasParent" in rel_type: return "sayou:hasChild"
        if "belongsTo" in rel_type: return "sayou:contains"
        return f"{rel_type}_REV"