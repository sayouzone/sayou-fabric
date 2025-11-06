# src/sayou/wrapper/interfaces/base_mapper.py
from abc import abstractmethod
from typing import List, Any, Dict
from sayou.core.base_component import BaseComponent
from sayou.wrapper.core.exceptions import MappingError

class BaseMapper(BaseComponent):
    """
    (Tier 1) 'Raw Data' 리스트를 '구조화된 dict' 리스트로 '매핑'하는
    모든 Mapper의 인터페이스. (Template Method)
    """
    component_name = "BaseMapper"
    
    def map_list(self, raw_data_list: List[Any]) -> List[Dict[str, Any]]:
        """
        [공통 골격] Raw Data 리스트를 순회하며 매핑을 실행합니다.
        Tier 2/3는 이 메서드를 오버라이드하지 않습니다.
        """
        self._log(f"Mapping {len(raw_data_list)} raw items...")
        mapped_dicts = []
        for raw_data in raw_data_list:
            try:
                # Tier 2/3가 '알맹이'를 구현
                mapped_dict = self._do_map_item(raw_data)
                if mapped_dict:
                    mapped_dicts.append(mapped_dict)
            except Exception as e:
                self._log(f"Mapping failed for item {raw_data}: {e}")
                # (정책에 따라 실패 시 중단하거나, None을 반환)
        
        self._log(f"Mapping complete. {len(mapped_dicts)} items mapped.")
        return mapped_dicts

    @abstractmethod
    def _do_map_item(self, raw_data_item: Any) -> Dict[str, Any]:
        """
        [구현 필수] 단일 원본 데이터 조각을 받아
        'DataAtom'의 기반이 될 딕셔너리로 매핑합니다.
        
        :param raw_data_item: e.g., CSV의 1행 (list)
        :return: DataAtom 구조를 가진 딕셔너리
                (e.g., {"source": "...", "type": "...", "payload": {...}})
        """
        raise NotImplementedError