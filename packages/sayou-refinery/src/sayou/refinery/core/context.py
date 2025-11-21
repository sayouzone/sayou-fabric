from dataclasses import dataclass, field
from typing import List, Dict, Any

from sayou.core.atom import DataAtom

@dataclass
class RefineryContext:
    """
    Refinery 파이프라인 실행 전반에 걸쳐 사용되는
    데이터 및 메타데이터 컨텍스트.
    """
    # 1. 파이프라인이 처리하는 핵심 데이터
    atoms: List[DataAtom]
    
    # 2. Merger가 사용할 '외부 조회' 데이터 (선택적)
    external_data: Dict[str, Any] = field(default_factory=dict)
    
    # (향후: user_id, run_id, logging_level 등 메타데이터 추가 가능)