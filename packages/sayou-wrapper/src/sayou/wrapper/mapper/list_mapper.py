# src/sayou/wrapper/templates/mapper/list_mapper.py
from typing import Dict, Any, List
from sayou.wrapper.interfaces.base_mapper import BaseMapper
from sayou.wrapper.core.exceptions import MappingError

class ListMapper(BaseMapper):
    """
    (Tier 2) 'List' (e.g., CSV row)를 'Dict'로 매핑하는 일반 엔진.
    사용자가 'main.py'에서 이 클래스에 '매핑 규칙'을 주입합니다.
    """
    component_name = "ListMapper"

    def initialize(self, **kwargs):
        """
        'main.py'에서 '매핑 규칙'을 주입받습니다.
        e.g., 
        field_mappings = {
            0: "payload.entity_id", # 0번 인덱스 -> entity_id
            1: "payload.attributes.schema:name" # 1번 인덱스 -> name
        }
        static_fields = {
            "source": "csv_connector",
            "type": "entity"
        }
        headers = ["id", "name"] (CSV 헤더가 있을 경우)
        """
        self.mappings = kwargs.get("field_mappings", {})
        self.static_fields = kwargs.get("static_fields", {})
        self.headers = kwargs.get("headers") # (선택적) 헤더 사용 시
        
        if not self.mappings:
            raise MappingError("ListMapper requires 'field_mappings'.")

    def _do_map_item(self, raw_data_item: List[Any]) -> Dict[str, Any]:
        """
        [Tier 1 구현] '매핑 규칙'에 따라 List를 Dict로 변환합니다.
        (e.g., ["222", "강남"] -> {"source": ..., "type": ..., "payload": {...}})
        """
        # 1. 고정 값(e.g., source, type)으로 뼈대 생성
        mapped_dict = self.static_fields.copy()

        # DataAtom의 'payload' 뼈대(attributes, relationships)를 '먼저' 생성합니다.
        # 이렇게 하면 매핑 규칙에 'relationships'가 없더라도
        # 'payload.relationships: {}'가 항상 존재하게 됩니다.
        mapped_dict.setdefault("payload", {})
        mapped_dict["payload"].setdefault("attributes", {})
        mapped_dict["payload"].setdefault("relationships", {})

        # 2. 매핑 규칙에 따라 값 삽입
        for index, value in enumerate(raw_data_item):
            key_path = None
            if self.headers:
                header_name = self.headers[index]
                key_path = self.mappings.get(header_name) # 헤더명 기준
            else:
                key_path = self.mappings.get(index) # 인덱스 기준
            
            if key_path:
                # e.g., "payload.attributes.schema:name" 같은 중첩 키 설정
                self._set_nested_value(mapped_dict, key_path.split('.'), value)
                
        return mapped_dict

    def _set_nested_value(self, d: Dict, keys: List[str], value: Any):
        """d[keys[0]][keys[1]]... = value를 안전하게 설정"""
        current = d
        for key in keys[:-1]:
            current = current.setdefault(key, {})
        current[keys[-1]] = value