from abc import abstractmethod
from collections import defaultdict
from typing import List, Any, Tuple

from sayou.core.atom import DataAtom

from ..core.context import RefineryContext
from ..interfaces.base_aggregator import BaseAggregator

class AverageAggregator(BaseAggregator):
    """
    (Tier 2) '평균'을 계산하는 '일반 로직' 엔진 (템플릿).
    
    이 클래스는 '평균 계산 템플릿'을 제공합니다.
    이 클래스를 상속받는 플러그인(Tier 3)은
    '무엇을', '어떻게' 그룹화할지만 정의합니다.
    """
    component_name = "AverageAggregator"

    # --- Template Method ---
    def aggregate(self, context: RefineryContext) -> RefineryContext: # 👈 입력이 context

        self._log(f"Starting averaging aggregation for {len(context.atoms)} atoms.")
        
        aggregator = defaultdict(lambda: {"_total": 0.0, "_count": 0})
        non_matching_atoms: List[DataAtom] = []

        processed_count = 0

        for atom in context.atoms:
            try:
                # 2. 자식(Tier 3)이 그룹핑 키를 결정
                grouping_keys = self._get_grouping_keys(atom)
                if grouping_keys is None: # 집계 대상 아님
                    non_matching_atoms.append(atom)
                    continue

                # 3. 자식(Tier 3)이 평균 낼 값을 가져옴
                values = self._get_values_to_average(atom)
                if values is None:
                    non_matching_atoms.append(atom)
                    continue

                # 4. 일반 로직: 버킷에 값 누적
                bucket = aggregator[grouping_keys]
                for value in values:
                    try:
                        bucket["_total"] += float(value)
                        bucket["_count"] += 1
                    except (ValueError, TypeError):
                        pass # 숫자가 아닌 값 무시
                processed_count += 1
            
            except Exception as e:
                self._log(f"Skipping atom {atom.atom_id} due to error: {e}")
                non_matching_atoms.append(atom)
                pass 

        self._log(f"Aggregated {processed_count} atoms into {len(aggregator)} groups.")
        
        # 5. 자식(Tier 3)이 집계 데이터로 최종 '신규 Atom' 생성
        newly_created_atoms: List[DataAtom] = []
        for group_keys, bucket in aggregator.items():
            count = bucket["_count"]
            if count > 0:
                average = bucket["_total"] / count
                new_atom = self._create_average_atom(
                    group_keys=group_keys, 
                    average_value=average, 
                    _total=bucket["_total"],
                    _count=count
                )
                if new_atom: newly_created_atoms.append(new_atom)
        
        # 👇 [산출물 0개 오류 수정] (통과된 Atom + 새로 생성된 Atom)
        context.atoms = non_matching_atoms + newly_created_atoms
        
        self._log(f"Aggregation complete. Final atom count: {len(context.atoms)}")
        return context

    # --- Abstract Methods (Tier 3가 구현할 부분) ---

    @abstractmethod
    def _get_grouping_keys(self, atom: DataAtom) -> Tuple | None:
        """
        Tier 3(e.g., SubwayRefiner)가 구현:
        이 Atom을 어떤 그룹에 속하게 할지 키의 '튜플'을 반환합니다.
        (e.g., ("station_222", "WEEKDAY"))
        집계 대상이 아니면 None을 반환합니다.
        """
        raise NotImplementedError

    @abstractmethod
    def _get_values_to_average(self, atom: DataAtom) -> List[Any] | None:
        """
        Tier 3(e.g., SubwayRefiner)가 구현:
        평균을 계산할 숫자 '리스트'를 Atom에서 추출하여 반환합니다.
        (e.g., return atom.payload["timeseries"].values())
        """
        raise NotImplementedError

    @abstractmethod
    def _create_average_atom(self, group_keys: Tuple, average_value: float, **kwargs) -> DataAtom | None:
        """
        Tier 3(e.g., SubwayRefiner)가 구현:
        계산된 평균값과 그룹 키를 바탕으로 '신규 DataAtom'을 생성합니다.
        """
        raise NotImplementedError