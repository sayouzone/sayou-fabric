from abc import abstractmethod
from typing import Dict, Any

from sayou.core.base_component import BaseComponent

from ..core.exceptions import AssemblerError
from ..graph.knowledge_graph import KnowledgeGraph

class BaseBuilder(BaseComponent):
    """
    (Tier 1) WrapperOutput(Standard Nodes)을 받아 KnowledgeGraph를 조립하는 인터페이스.
    """
    component_name = "BaseBuilder"

    def _build(self, wrapper_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        [Public API] Wrapper 결과를 받아 그래프(Dict)로 반환.
        """
        self._log("Starting assembly process...")
        try:
            # 1. 실제 조립 (Tier 2)
            kg_obj = self.build(wrapper_output)
            
            # 2. 결과 반환 (Dict)
            return kg_obj.to_dict()
            
        except Exception as e:
            raise AssemblerError(f"Assembly failed in {self.component_name}: {e}")

    @abstractmethod
    def build(self, data: Dict[str, Any]) -> KnowledgeGraph:
        """[구현 필수]"""
        raise NotImplementedError