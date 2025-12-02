import re
from typing import List

from ..core.schemas import Chunk, InputDocument
from ..splitter.recursive_splitter import RecursiveSplitter
from ..utils.text_segmenter import TextSegmenter


class StructureSplitter(RecursiveSplitter):
    component_name = "StructureSplitter"
    SUPPORTED_TYPES = ["structure"]

    def _do_split(self, doc: InputDocument) -> List[Chunk]:
        config = doc.metadata.get("config", {})
        chunk_size = config.get("chunk_size", 1000)

        structure_pattern = config.get("structure_pattern", r"\n\n")

        try:
            split_regex = f"(?m)(?={structure_pattern})"
            sections = re.split(split_regex, doc.content)
        except Exception:
            sections = doc.content.split("\n\n")

        final_chunks = []

        for section in sections:
            section = section.strip()
            if not section:
                continue

            if len(section) > chunk_size:
                sub_parts = TextSegmenter.split_with_protection(
                    section,
                    config.get("separators", self.DEFAULT_SEPARATORS),
                    config.get("protected_patterns", []),
                    chunk_size,
                    config.get("chunk_overlap", 50),
                )
                for part in sub_parts:
                    final_chunks.append(
                        Chunk(chunk_content=part, metadata=doc.metadata)
                    )
            else:
                final_chunks.append(Chunk(chunk_content=section, metadata=doc.metadata))

        return final_chunks
