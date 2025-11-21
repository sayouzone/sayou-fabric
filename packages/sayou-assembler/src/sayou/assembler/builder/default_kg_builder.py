from typing import List
from collections import defaultdict

from sayou.core.atom import DataAtom

from ..core.exceptions import BuildError
from ..interfaces.base_builder import BaseBuilder
from ..utils.graph_model import KnowledgeGraph

class DefaultKGBuilder(BaseBuilder):
    """
    (Tier 2) '일반 KG' 구축 엔진.
    Atom을 받아 인메모리 KnowledgeGraph 객체를 생성하고 링킹합니다.
    """
    component_name = "DefaultKGBuilder"

    def initialize(self, **kwargs):
        # TODO: 향후 스키마 기반 '정방향' 링커 등을 여기서 초기화
        self._log("DefaultKGBuilder initialized.")
        pass

    def build(self, atoms: List[DataAtom]) -> KnowledgeGraph:
        """Atom을 KG로 구축하고, 역방향 링크를 생성합니다."""
        try:
            self._log(f"Building {len(atoms)} atoms into KnowledgeGraph...")
            
            # 1. Atom에서 엔티티 생성 (구 builder.py)
            entities = self.build_entities_from_atoms(atoms)
            graph = KnowledgeGraph(entities=entities)
            self._log(f"Built {len(graph)} initial entities.")
            
            # 2. 역방향 링크 생성 (구 linker.py)
            linked_graph = self.link_reverse_relationships(graph)
            self._log("Reverse linking complete.")
            
            return linked_graph
        
        except Exception as e:
            raise BuildError(f"Failed during KG build process: {e}")

    def build_entities_from_atoms(self, atoms, refined_nodes={}) -> dict:
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

    def link_reverse_relationships(self, graph: KnowledgeGraph) -> KnowledgeGraph:
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