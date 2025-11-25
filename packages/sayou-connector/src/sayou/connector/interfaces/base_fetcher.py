from abc import abstractmethod

from ..core.models import FetchTask, FetchResult

from sayou.core.base_component import BaseComponent

class BaseFetcher(BaseComponent):
    """
    (Tier 1) 실제 데이터를 가져오는 드라이버.
    Generator가 준 Task 명세대로 수행만 함.
    """
    component_name = "BaseFetcher"
    SUPPORTED_TYPES = []

    @abstractmethod
    def fetch(self, task: FetchTask) -> FetchResult:
        raise NotImplementedError