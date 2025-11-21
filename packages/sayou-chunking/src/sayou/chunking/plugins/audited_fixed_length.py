from typing import List, Dict, Any

from ..splitter.fixed_length import FixedLengthSplitter

class AuditedFixedLengthSplitter(FixedLengthSplitter):
    """
    (Tier 3 - 플러그인) 'FixedLengthSplitter'(T2)의 기본 기능을
    그대로 사용하되(super), 결과 메타데이터에 '감사' 태그를 추가합니다.
    """
    component_name = "AuditedFixedLengthSplitter"
    
    # T2와 '다른' 타입을 정의하여 T2와 공존합니다.
    SUPPORTED_TYPES = ["fixed_length_audited"] 

    def initialize(self, **kwargs):
        """T2의 초기화 로직을 먼저 호출합니다."""
        super().initialize(**kwargs)
        self._audit_tag = kwargs.get("audit_tag", "audited_by_sayou_plugin")
        self._log(f"AuditedFixedLengthSplitter (Plugin) is ready. Tag: {self._audit_tag}")

    def _do_split(self, split_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        [Tier 1 구현]
        T2의 '_do_split'을 호출하여 기본 청킹을 수행하고,
        반환된 결과에 '추가' 작업을 수행합니다. (Decorator 패턴)
        """
        
        # 1. T2(부모)의 분할 로직을 그대로 호출하여 결과를 받음
        default_chunks = super()._do_split(split_request)
        
        # 2. 결과물에 '추가' 작업 (e.g., 메타데이터 수정)
        for chunk in default_chunks:
            if "metadata" not in chunk:
                chunk["metadata"] = {}
            chunk["metadata"]["audit_tag"] = self._audit_tag
            
        return default_chunks