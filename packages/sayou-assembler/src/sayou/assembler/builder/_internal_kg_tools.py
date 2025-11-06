from collections import defaultdict
from sayou.assembler.utils.graph_model import KnowledgeGraph

"""
(Tier 2 Helper) 
이 파일은 default_kg_builder.py만 사용하는 비공개 내부 로직입니다.
(구 graph/builder.py와 linker/default_linker.py의 핵심 로직)
"""

def build_entities_from_atoms(atoms, refined_nodes={}) -> dict:
    """Atom 리스트에서 기본 엔티티 딕셔너리를 생성합니다."""
    entities = {}
    for atom in atoms:
        payload = atom.payload
        eid = payload.get("entity_id")
        if not eid or not payload.get("entity_class"):
            continue

        entities[eid] = {
            "class": payload.get("entity_class"),
            "friendly_name": payload.get("friendly_name", eid),
            "attributes": payload.get("attributes", {}),
            "relationships": payload.get("relationships", {}),
            "relationships_reverse": defaultdict(list)
        }
    
    # (Refinery가 생성한) 정제된 노드 병합
    for eid, node_data in refined_nodes.items():
        entities[eid] = {
            "class": node_data.get("class"),
            "friendly_name": node_data.get("friendly_name", eid),
            "attributes": node_data.get("attributes", {}),
            "relationships": node_data.get("relationships", {}),
            "relationships_reverse": defaultdict(list)
        }
    return entities

def link_reverse_relationships(graph: KnowledgeGraph) -> KnowledgeGraph:
    """그래프 엔티티들의 역방향 관계를 생성합니다."""
    entities = graph.entities
    processed = 0
    for eid, node in entities.items():
        for pred, targets in node.get("relationships", {}).items():
            if isinstance(targets, str):
                targets = [targets]
            
            for tid in targets:
                if tid not in entities:
                    continue
                
                rev_pred = f"{pred}_by"
                if eid not in entities[tid]["relationships_reverse"][rev_pred]:
                    entities[tid]["relationships_reverse"][rev_pred].append(eid)
                    processed += 1
    # self._log(f"{processed} reverse links generated.") # (Logging은 호출자가)
    return graph