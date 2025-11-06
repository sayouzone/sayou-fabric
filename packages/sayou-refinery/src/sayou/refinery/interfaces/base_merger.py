from abc import abstractmethod
from typing import List, Dict, Any
from sayou.core.base_component import BaseComponent
from sayou.refinery.core.context import RefineryContext
from sayou.core.atom import DataAtom

class BaseMerger(BaseComponent):
    """
    (Tier 1) Atom 리스트와 '외부 데이터'를 '병합(Merge)'하여
    Atom을 '강화(Enrich)'하는 모든 Refiner의 인터페이스.
    """
    component_name = "BaseMerger"

    @abstractmethod
    def merge(self, context: RefineryContext) -> RefineryContext:
        """
        Atom 리스트와 외부에서 '조회(Retrieve)'된 데이터 딕셔너리를 입력받아,
        두 데이터를 병합하여 '강화된' Atom 리스트를 반환합니다.

        :param context: 전체 실행 컨텍스트
        :return: 수정된 실행 컨텍스트
        """
        raise NotImplementedError