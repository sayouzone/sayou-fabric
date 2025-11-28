from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SayouTask(BaseModel):
    source_type: str = Field(..., description="Fetcher 라우팅 키 (e.g., 'file', 'http', 'sqlite')")
    uri: str = Field(..., description="접근 경로 (File Path, URL, DB Connection String)")
    params: Dict[str, Any] = Field(default_factory=dict, description="선택자, 쿼리, 옵션 등 상세 설정")
    meta: Dict[str, Any] = Field(default_factory=dict, description="파일명, 오프셋 등 보조 정보")

class SayouPacket(BaseModel):
    task: Optional[SayouTask] = Field(None, description="이 패킷을 생성한 원본 지시서")
    created_at: datetime = Field(default_factory=datetime.now, description="패킷 생성 시간")
    success: bool = Field(True, description="작업 성공 여부")
    error: Optional[str] = Field(None, description="실패 시 에러 메시지")
    data: Any = Field(None, description="단계별 처리 데이터 (Type: Any)")
    meta: Dict[str, Any] = Field(default_factory=dict, description="파이프라인 제어용 메타데이터")

    class Config:
        arbitrary_types_allowed = True

class SayouData(BaseModel):
    data_id: str
    content: Any
    source_metadata: Dict[str, Any] = Field(default_factory=dict)
    process_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)

class SayouNode(BaseModel):
    node_id: str = Field(..., description="Unique Identifier")
    node_class: str = Field(..., description="Ontology Class")
    friendly_name: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    relationships: Dict[str, List[str]] = Field(default_factory=dict)

class SayouDataset(BaseModel):
    nodes: List[SayouNode]
    metadata: Dict[str, Any] = Field(default_factory=dict)