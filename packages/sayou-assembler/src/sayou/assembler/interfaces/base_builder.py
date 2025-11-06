from abc import abstractmethod
from typing import List, Any
from sayou.core.base_component import BaseComponent
from sayou.core.atom import DataAtom

class BaseBuilder(BaseComponent):
    """
    (Tier 1) Atom 리스트를 받아 특정 인메모리 객체로 '구축(Build)'하는
    모든 빌더의 인터페이스.
    """
    component_name = "BaseBuilder"

    @abstractmethod
    def build(self, atoms: List[DataAtom]) -> Any:
        """
        Atom 리스트를 받아 특정 구조(e.g., KnowledgeGraph, VectorIndex)를 
        인메모리에 구축하고 그 객체를 반환합니다.
        
        :param atoms: 유효성이 검증된 DataAtom 리스트
        :return: 구축된 객체 (e.g., KnowledgeGraph 인스턴스)
        """
        raise NotImplementedError