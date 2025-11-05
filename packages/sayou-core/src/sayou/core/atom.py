import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, Any

@dataclass
class DataAtom:
    """
    (Tier 0) '사유존' 툴킷 생태계의 표준 데이터 컨테이너.
    모든 컴포넌트가 '스키마' 기반으로 소통하는 표준 화폐입니다.
    """
    source: str
    type: str
    payload: Dict[str, Any]
    
    atom_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """dataclass를 딕셔너리로 변환합니다."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        """JSON 등 딕셔너리에서 DataAtom 객체를 생성합니다."""
        if "source" not in data or "type" not in data or "payload" not in data:
            # DataAtom은 'sayou-core'에 의존하므로 SayouCoreError 사용
            from .exceptions import SayouCoreError 
            raise SayouCoreError("Missing required fields (source, type, payload) in data.")
            
        return cls(
            source=data["source"],
            type=data["type"],
            payload=data["payload"],
            atom_id=data.get("atom_id", str(uuid.uuid4())),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat())
        )