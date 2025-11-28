from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

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