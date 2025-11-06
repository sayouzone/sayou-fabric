from abc import abstractmethod
from typing import List
from sayou.core.base_component import BaseComponent
from sayou.core.atom import DataAtom
from sayou.refinery.core.context import RefineryContext

class BaseProcessor(BaseComponent):
    """
    (Tier 1) Atom을 1:1로 '처리(Process)'하는 모든 Refiner의 인터페이스.
    (e.g., HTML 클리닝, 데이터 Fetch, PII 마스킹)
    """
    component_name = "BaseProcessor"

    @abstractmethod
    def process(self, context: RefineryContext) -> RefineryContext:
        """
        Atom 리스트를 받아, 각 Atom을 1:1로 처리(변환)한
        '새로운' Atom 리스트를 반환합니다.

        :param context: 전체 실행 컨텍스트
        :return: 수정된 실행 컨텍스트
        """
        raise NotImplementedError