from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class SayouNode(BaseModel):
    node_id: str = Field(..., description="Unique Identifier")
    node_class: str = Field(..., description="Ontology Class")
    friendly_name: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    relationships: Dict[str, List[str]] = Field(default_factory=dict)

class SayouDataset(BaseModel):
    nodes: List[SayouNode]
    metadata: Dict[str, Any] = Field(default_factory=dict)