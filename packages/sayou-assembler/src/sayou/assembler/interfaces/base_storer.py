from abc import abstractmethod
from typing import Any

from sayou.core.base_component import BaseComponent

class BaseStorer(BaseComponent):
    """
    (Tier 1) '구축(Build)'된 인메모리 객체를 
    특정 저장소(DB, File)에 '저장(Store)'하는 모든 스토어의 인터페이스.
    """
    component_name = "BaseStorer"

    @abstractmethod
    def store(self, built_object: Any):
        """
        Builder가 생성한 객체를 받아 영구 저장소에 저장합니다.
        
        :param built_object: Builder가 반환한 객체 (e.g., KnowledgeGraph 인스턴스)
        """
        raise NotImplementedError