import re
from typing import Any, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock, SayouChunk

from ..interfaces.base_splitter import BaseSplitter
from ..utils.text_segmenter import TextSegmenter


@register_component("splitter")
class StructureSplitter(BaseSplitter):
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
            import re

            if re.search(r"(?m)^#{1,6}\s", input_data) or "```" in input_data:
                return 0.95

            if "#" in input_data and "Title" in input_data:
                return 0.9

        if hasattr(input_data, "type") and input_data.type in ["md", "markdown"]:
            return 1.0

        return 0.0

    def _do_split(self, doc: SayouBlock) -> List[SayouChunk]:
        config = doc.metadata.get("config", {})
        doc_id = doc.metadata.get("id", "doc")
        chunk_size = config.get("chunk_size", 1000)

        structure_pattern = config.get("structure_pattern", r"\n\n")

        try:
            split_regex = f"(?m)(?={structure_pattern})"
            sections = re.split(split_regex, doc.content)
        except Exception:
            sections = doc.content.split("\n\n")

        final_chunks = []

        for i, section in enumerate(sections):
            section = section.strip()
            if not section:
                continue

            base_meta = doc.metadata.copy()
            base_meta["parent_structure_idx"] = i

            if len(section) > chunk_size:
                sub_parts = TextSegmenter.split_with_protection(
                    text=section,
                    separators=config.get("separators", self.DEFAULT_SEPARATORS),
                    protected_patterns=config.get("protected_patterns", []),
                    chunk_size=chunk_size,
                    chunk_overlap=config.get("chunk_overlap", 50),
                )
                for j, part in enumerate(sub_parts):
                    meta = base_meta.copy()
                    meta.update(
                        {
                            "chunk_id": f"{doc_id}_s{i}_p{j}",
                            "chunk_size": len(part),
                        }
                    )
                    final_chunks.append(SayouChunk(content=part, metadata=meta))
            else:
                base_meta.update(
                    {
                        "chunk_id": f"{doc_id}_s{i}",
                        "chunk_size": len(section),
                    }
                )
                final_chunks.append(SayouChunk(content=section, metadata=base_meta))

        return final_chunks
