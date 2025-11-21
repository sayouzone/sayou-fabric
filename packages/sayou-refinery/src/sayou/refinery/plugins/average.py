import re
from typing import List, Any, Tuple

from sayou.core.atom import DataAtom

from ..aggregator.average import AverageAggregator

def get_day_type(date_str: str) -> str:
    from datetime import datetime
    try:
        weekday = datetime.strptime(date_str, "%Y-%m-%d").weekday()
        if weekday >= 5: return "WEEKEND"
        return "WEEKDAY"
    except:
        return "UNKNOWN"

class SubwayAverageRefiner(AverageAggregator):
    """
    (Tier 3) '지하철 승하차' Atom의 '평균'을 계산하는 특화 플러그인.
    Tier 2(AverageAggregator)를 상속받아 3개의 추상 메서드만 구현.
    """
    component_name = "SubwayAverageRefiner"
    
    def initialize(self, **kwargs):
        self._date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}")
        self._log("SubwayAverageRefiner initialized.")

    # --- Tier 2 추상 메서드 구현 ---

    def _get_grouping_keys(self, atom: DataAtom) -> Tuple | None:
        """'지하철' 데이터에서 (역 ID, 요일 타입, 승/하차 구분)을 키로 추출"""
        payload = atom.payload
        if atom.type != "ridership": # 'ridership' Atom만 집계
            return None

        station_id = payload.get("relationships", {}).get("sayou:observedAt")
        date_match = self._date_pattern.search(payload.get("friendly_name", ""))
        
        if not (station_id and date_match): return None # 그룹핑 불가

        date_str = date_match.group(0)
        day_type = get_day_type(date_str)
        obs_type = payload.get("attributes", {}).get("sayou:observationType")
        
        if not obs_type: return None
        
        return (station_id, day_type, obs_type)

    def _get_values_to_average(self, atom: DataAtom) -> List[Any] | None:
        """'지하철' 데이터에서 '시계열 데이터의 값들'을 리스트로 추출"""
        timeseries = atom.payload.get("attributes", {}).get("sayou:hasTimeSeriesData", {})
        if not timeseries:
            return None
        return list(timeseries.values()) # e.g., [100, 200, 500]

    def _create_average_atom(self, group_keys: Tuple, average_value: float, **kwargs) -> DataAtom:
        """'평균 지하철 승하차' Atom을 생성"""
        station_id, day_type, obs_type = group_keys
        
        # (참고: 이 예제는 '일일 총 승객수'의 평균을 계산합니다.
        #  '시간대별' 평균을 내려면 Tier 2의 AverageAggregator 로직 수정이 필요합니다.)
        
        avg_type_map = {
            "transit:boarding": "average_boarding_total",
            "transit:alighting": "average_alighting_total"
        }
        
        new_atom_payload = {
            "entity_id": f"sayou:obs:avg:{station_id}:{day_type}:{obs_type}",
            "entity_class": "sayou:AverageObservation",
            "friendly_name": f"일일 평균 관측 ({station_id}/{day_type}/{obs_type})",
            "attributes": {
                "sayou:observationType": avg_type_map.get(obs_type, "average"),
                "sayou:dayType": day_type,
                "sayou:averageTotalValue": round(average_value, 2),
                "sayou:sourceCount": kwargs.get('count', 0)
            },
            "relationships": {
                "sayou:observedAt": station_id
            }
        }
        
        return DataAtom(
            source=self.component_name,
            type="refined_average",
            payload=new_atom_payload
        )