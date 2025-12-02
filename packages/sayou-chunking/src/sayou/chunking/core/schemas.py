from typing import Any, Dict

from pydantic import BaseModel, Field


class InputDocument(BaseModel):
    """
    Standardized input model for splitters.

    Acts as a normalized container for the raw content and its metadata
    before the splitting logic begins.
    """

    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Chunk(BaseModel):
    """
    The atomic unit of data produced by the chunking process.

    Contains the split text segment and associated metadata (e.g., source ID,
    semantic type, parent ID). This is the final output ready for embedding.
    """

    chunk_content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def update_metadata(self, **kwargs):
        self.metadata.update(kwargs)
