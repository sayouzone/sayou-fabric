import re
from typing import Any, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock, SayouChunk

from ..splitter.recursive_splitter import RecursiveSplitter
from ..utils.text_segmenter import TextSegmenter


@register_component("splitter")
class StructureSplitter(RecursiveSplitter):
    """
    Regex-based Structure Splitter.

    Uses a user-defined regex pattern (e.g., 'Article \d+') to identify
    structural boundaries in the document and splits along those lines first.
    """

    component_name = "StructureSplitter"
    SUPPORTED_TYPES = ["structure"]

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        if strategy in ["structure"]:
            return 1.0

        if isinstance(input_data, list) and len(input_data) > 0:
            first = input_data[0]
            if hasattr(first, "type") and first.type in [
                "md",
                "markdown",
                "html",
                "table",
            ]:
                return 0.95

        if isinstance(input_data, str):
            if (
                re.search(r"(?m)^#{1,6}\s", input_data)
                or "```" in input_data
                or re.search(r"<[^>]+>", input_data)
            ):
                return 0.9

        return 0.0

    def _do_split(self, doc: SayouBlock) -> List[SayouChunk]:
        """
        Split by structure regex first, then fall back to recursive splitting
        for sections larger than `chunk_size`.
        """
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
                    final_chunks.append(SayouChunk(content=part, metadata=doc.metadata))
            else:
                final_chunks.append(SayouChunk(content=section, metadata=doc.metadata))

        return final_chunks
