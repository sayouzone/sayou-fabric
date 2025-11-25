from abc import abstractmethod
from typing import Iterator

from ..core.models import FetchTask, FetchResult

from sayou.core.base_component import BaseComponent

class BaseGenerator(BaseComponent):
    """
    (Tier 1) '무엇을 수집할지' 결정하는 네비게이터.
    Iterator 프로토콜을 따르며, Fetch 결과를 피드백 받아 다음 경로를 수정할 수도 있음.
    """
    component_name = "BaseGenerator"
    SUPPORTED_TYPES = []

    @abstractmethod
    def generate(self) -> Iterator[FetchTask]:
        """
        [Generator] 수집할 Task를 하나씩 생성하여 반환(yield)합니다.
        """
        raise NotImplementedError

    def feedback(self, result: FetchResult):
        """
        (Optional) Fetcher의 결과를 보고 다음 탐색 전략을 수정해야 할 때 사용.
        예: 웹 크롤러(HTML에서 링크 추출), API(다음 페이지 토큰 확인)
        """
        pass