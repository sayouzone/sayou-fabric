from typing import Any, Dict, List, Union

from pydantic import BaseModel, Field


class ContentBlock(BaseModel):
    """
    Standard unit of content refined from raw data.

    Refinery normalizes raw inputs into a list of these blocks.
    Processors iterate over these blocks to clean or modify them.
    """

    type: str = Field(
        ..., description="Block type (e.g., 'text', 'md', 'record', 'table')"
    )

    content: Union[str, Dict[str, Any], List[Any]] = Field(
        ..., description="The actual data payload"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Context info (page_num, source_id, etc.)"
    )

    class Config:
        arbitrary_types_allowed = True
