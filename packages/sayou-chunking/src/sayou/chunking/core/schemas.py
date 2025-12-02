from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class InputDocument(BaseModel):

    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Chunk(BaseModel):

    chunk_content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def update_metadata(self, **kwargs):
        self.metadata.update(kwargs)
