from typing import List

from ..core.schemas import Chunk, InputDocument
from ..interfaces.base_splitter import BaseSplitter


class FixedLengthSplitter(BaseSplitter):
    component_name = "FixedLengthSplitter"
    SUPPORTED_TYPES = ["fixed_length"]

    def _do_split(self, doc: InputDocument) -> List[Chunk]:
        config = doc.metadata.get("config", {})
        chunk_size = config.get("chunk_size", 1000)
        chunk_overlap = config.get("chunk_overlap", 0)
        content = doc.content

        text_chunks = []
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        step = chunk_size - chunk_overlap
        for i in range(0, len(content), step):
            text_chunks.append(content[i : i + chunk_size])

        return [Chunk(chunk_content=t, metadata=doc.metadata) for t in text_chunks]
