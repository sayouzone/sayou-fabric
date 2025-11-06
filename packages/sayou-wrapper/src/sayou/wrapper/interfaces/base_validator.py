# src/sayou/wrapper/interfaces/base_validator.py
from abc import abstractmethod
from typing import List, Dict, Any
from sayou.core.base_component import BaseComponent

class BaseValidator(BaseComponent):
    """
    (Tier 1) '매핑된 dict' 리스트가 스키마에 부합하는지 '검증'하는
    모든 Validator의 인터페이스. (Template Method)
    """
    component_name = "BaseValidator"
    
    def validate_list(self, mapped_dicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        [공통 골격] 매핑된 dict 리스트를 순회하며 검증합니다.
        Tier 2/3는 이 메서드를 오버라이드하지 않습니다.
        """
        self._log(f"Validating {len(mapped_dicts)} mapped items...")
        validated_dicts = []
        for mapped_dict in mapped_dicts:
            try:
                # Tier 2/3가 '알맹이'를 구현
                if self._do_validate_item(mapped_dict):
                    validated_dicts.append(mapped_dict)
                else:
                    # (실패 시 로그만 남기고 필터링)
                    self._log(f"Validation failed, item dropped: {mapped_dict.get('payload', {}).get('entity_id', 'N/A')}")
            except Exception as e:
                self._log(f"Validation error: {e}")

        self._log(f"Validation complete. {len(validated_dicts)} items passed.")
        return validated_dicts

    @abstractmethod
    def _do_validate_item(self, mapped_dict: Dict[str, Any]) -> bool:
        """
        [구현 필수] 단일 매핑 딕셔너리를 검증합니다.
        
        :param mapped_dict: Mapper가 생성한 딕셔너리
        :return: (True/False) 검증 통과 여부
        """
        raise NotImplementedError