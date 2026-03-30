from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

# ==============================================================================
# 1. Ingestion Stage (Connector)
# ==============================================================================


class SayouTask(BaseModel):
    """
    [Input] Defines a unit of work for the Connector.

    Generators produce these tasks (e.g. "download this URL") and Fetchers
    execute them.
    """

    source_type: str = Field(..., description="Routing key (e.g. 'file', 'http')")
    uri: str = Field(..., description="Resource location")
    params: Dict[str, Any] = Field(
        default_factory=dict, description="Execution parameters"
    )
    meta: Dict[str, Any] = Field(default_factory=dict, description="Context metadata")


class SayouPacket(BaseModel):
    """
    [Transport] Universal container for raw data transport.

    Produced by the Connector, this packet carries the raw payload (bytes,
    str, or dict) safely across pipeline boundaries.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    task: Optional[SayouTask] = Field(
        None, description="The task that originated this packet"
    )
    data: Any = Field(None, description="Raw payload (bytes, str, or dict)")
    success: bool = Field(True, description="Operation status")
    error: Optional[str] = Field(None, description="Error message if failed")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Process metadata")
    created_at: datetime = Field(default_factory=datetime.now)


# ==============================================================================
# 2. Refinement Stage (Refinery output)
# ==============================================================================


class SayouBlock(BaseModel):
    """
    [Intermediate] The atomic unit of content (text / image / record).

    Refinery normalises raw data into these blocks.  Chunking subsequently
    splits them into smaller pieces.
    """

    type: str = Field(
        ..., description="Content type (e.g. 'text', 'md', 'record', 'image')"
    )
    content: Union[str, Dict[str, Any], List[Any]] = Field(
        ..., description="Actual content payload"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Source context (page, lineage)"
    )


# ==============================================================================
# 3. Chunking Stage (Chunking output)
# ==============================================================================


class SayouChunk(BaseModel):
    """
    [Intermediate] A segmented text unit ready for embedding.

    ChunkingPipeline splits a ``SayouBlock`` into multiple ``SayouChunk``s.
    """

    content: str = Field(..., description="The split text segment")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Context (chunk_id, parent_id, source, …)",
    )

    def update_metadata(self, **kwargs) -> None:
        """Update metadata fields in-place."""
        self.metadata.update(kwargs)


# ==============================================================================
# 4. Knowledge Graph Stage (Wrapper / Assembler / Loader)
# ==============================================================================


class SayouNode(BaseModel):
    """
    [Atom] The standard knowledge entity ready for a graph or vector store.

    WrapperPipeline converts ``SayouChunk``s into these nodes, assigning
    ontology classes and identifying relationships.

    Vector storage
    ──────────────
    The ``vector`` field is the canonical location for embedding vectors.
    ``EmbeddingAdapter`` writes here; ``VectorBuilder`` reads from here
    (falling back to ``attributes["vector"]`` for legacy payloads).
    """

    node_id: str = Field(..., description="Unique URI-style identifier")
    node_class: str = Field(..., description="Ontology class (e.g. 'sayou:Topic')")
    friendly_name: Optional[str] = Field(None, description="Human-readable label")
    attributes: Dict[str, Any] = Field(
        default_factory=dict, description="Node properties / values"
    )
    relationships: Dict[str, List[str]] = Field(
        default_factory=dict, description="Typed links to other node IDs"
    )
    vector: Optional[List[float]] = Field(
        None,
        description=(
            "Embedding vector (canonical location). "
            "Set by EmbeddingAdapter; read by VectorBuilder and vector-DB writers."
        ),
    )


class SayouOutput(BaseModel):
    """
    [Output] Final container for assembled knowledge.

    AssemblerPipeline produces this; LoaderPipeline consumes it.
    """

    nodes: List[SayouNode] = Field(
        default_factory=list, description="List of knowledge entities"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Global context metadata"
    )
