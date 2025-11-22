from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class Document:
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Chunk:
    chunk_content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_metadata(self, **kwargs):
        self.metadata.update(kwargs)