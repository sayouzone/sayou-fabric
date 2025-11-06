from typing import List, Any
from sayou.core.atom import DataAtom
from sayou.assembler.core.exceptions import BuildError
from sayou.assembler.interfaces.base_builder import BaseBuilder
from sayou.assembler.utils.graph_model import KnowledgeGraph
from ._internal_kg_tools import build_entities_from_atoms, link_reverse_relationships

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
            entities = build_entities_from_atoms(atoms)
            graph = KnowledgeGraph(entities=entities)
            self._log(f"Built {len(graph)} initial entities.")
            
            # 2. 역방향 링크 생성 (구 linker.py)
            linked_graph = link_reverse_relationships(graph)
            self._log("Reverse linking complete.")
            
            return linked_graph
        
        except Exception as e:
            raise BuildError(f"Failed during KG build process: {e}")