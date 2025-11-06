# src/sayou/wrapper/templates/validator/default_validator.py
from sayou.wrapper.interfaces.base_validator import BaseValidator
from sayou.wrapper.core.exceptions import ValidationError
from typing import Dict, Any

# (v.0.0.1 에서는 가벼운 '필수 키' 검증기)
# (v.0.1.0 에서는 'pip install jsonschema' 의존성을 추가하고
#  '사유존 온톨로지'를 JSON Schema로 변환하여 실제 검증 수행)

class DefaultValidator(BaseValidator):
    """
    (Tier 2) '매핑된 dict'를 검증하는 일반 엔진.
    v.0.0.1 에서는 'source', 'type', 'payload.entity_id' 존재만 검사.
    """
    component_name = "DefaultValidator"
    
    def initialize(self, **kwargs):
        self.ontology_path = kwargs.get("ontology_path")
        # (v.0.1.0: 여기서 온톨로지를 로드하고 JSON Schema로 컴파일)
        self._log(f"Initialized (v.0.0.1 - Basic Key Check mode).")

    def _do_validate_item(self, mapped_dict: Dict[str, Any]) -> bool:
        """[Tier 1 구현] 필수 키 존재 여부 검사"""
        
        if not mapped_dict.get("source") or not mapped_dict.get("type"):
            self._log(f"Validation failed: Missing 'source' or 'type'.")
            return False
            
        if not mapped_dict.get("payload", {}).get("entity_id"):
            self._log(f"Validation failed: Missing 'payload.entity_id'.")
            return False
            
        # (v.0.1.0: jsonschema.validate(mapped_dict, self.compiled_schema))
        return True