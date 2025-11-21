from abc import abstractmethod

from sayou.core.base_component import BaseComponent

from ..core.context import RefineryContext

class BaseAggregator(BaseComponent):
    """
    (Tier 1) 다수의 Atom을 '집계(Aggregate)'하여
    새로운 Atom을 생성하는 모든 Refiner의 인터페이스.
    (e.g., 평균 계산, 합계 계산)
    """
    component_name = "BaseAggregator"

    @abstractmethod
    def aggregate(self, context: RefineryContext) -> RefineryContext:
        """
        Atom 리스트를 받아, 이를 집계한 '새로운' 요약 Atom 리스트를 반환합니다.
        (N -> M, M은 N보다 작거나 같음)

        :param context: 전체 실행 컨텍스트
        :return: 수정된 실행 컨텍스트
        """
        raise NotImplementedError