from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class SayouNode(BaseModel):
    """
    (Schema) Sayou Platform의 모든 데이터가 지향해야 할 표준 '원자(Atom)'.
    이 구조로 변환되어야만 Assembler가 그래프로 조립할 수 있습니다.
    """
    # 1. 식별자 (URI) - e.g., "sayou:doc:123_part_0"
    node_id: str = Field(..., description="Unique Identifier for Graph DB")
    
    # 2. 타입 (Class) - e.g., "sayou:Topic", "sayou:Table"
    node_class: str = Field(..., description="Ontology Class Definition")
    
    # 3. 가독성 이름 (Optional)
    friendly_name: Optional[str] = None
    
    # 4. 동적 속성 (Attributes) - e.g., {"schema:text": "...", "finance:price": 100}
    attributes: Dict[str, Any] = Field(default_factory=dict)
    
    # 5. 관계 (Relationships) - e.g., {"sayou:hasParent": ["sayou:doc:123_h_0"]}
    relationships: Dict[str, List[str]] = Field(default_factory=dict)

class WrapperOutput(BaseModel):
    """Wrapper의 최종 산출물 컨테이너"""
    nodes: List[SayouNode]
    metadata: Dict[str, Any] = Field(default_factory=dict)