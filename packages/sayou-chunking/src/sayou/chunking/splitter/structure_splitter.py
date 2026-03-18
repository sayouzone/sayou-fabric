import re
from typing import Any, Dict, List

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

    DEFAULT_SEPARATORS = ["\n\n", "\n", r"(?<=[.?!])\s+", " ", ""]

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        if strategy in ["structure"]:
            return 1.0

        if isinstance(input_data, SayouBlock):
            if input_data.type in ["md", "markdown"]:
                return 0.9

            if input_data.type in ["html", "table", "json"]:
                return 0.9

            content = input_data.content
            if isinstance(content, str):
                if content.strip().startswith(("<html", "<!DOCTYPE", "<div")):
                    return 0.8
                if "```" in content or "~~~" in content:
                    return 0.8

        return 0.0

    def _do_split(self, doc: SayouBlock) -> List[SayouChunk]:
        """
        Main routing logic: Text vs Record.
        """
        # Case 1: Record Splitting (List of Dicts)
        if doc.type == "record" and isinstance(doc.content, list):
            return self._split_records(doc)

        # Case 2: Text Splitting (String)
        return self._split_text(doc)

    # --------------------------------------------------------------------------
    # Mode 2: Record Splitting Logic (for YouTube, Logs, CSV)
    # --------------------------------------------------------------------------
    def _split_records(self, doc: SayouBlock) -> List[SayouChunk]:
        config = doc.metadata.get("config", {})
        doc_id = doc.metadata.get("id", "doc")

        records = doc.content
        if not records:
            return []

        # [Option 1] Chapter-based
        chapter_intervals = config.get(
            "chapter_intervals", []
        )  # [(start, end, title), ...]

        if chapter_intervals:
            return self._group_by_intervals(records, chapter_intervals, doc)

        # [Option 2] Window-based
        # e.g. config={"window_size": 300, "window_key": "start"}
        window_size = config.get("window_size")
        window_key = config.get("window_key", "start")

        if window_size and window_key:
            return self._group_by_window(records, window_key, window_size, doc)

        return [
            self._create_chunk_from_records(records, doc.metadata, f"{doc_id}_full")
        ]

    def _group_by_intervals(
        self, records: List[Dict], intervals: List, doc: SayouBlock
    ) -> List[SayouChunk]:
        """
        Groups records based on provided time intervals (Chapters).
        """
        chunks = []
        doc_id = doc.metadata.get("id", "doc")
        time_key = "start"
        current_interval_idx = 0
        current_group = []

        for record in records:
            t = float(record.get(time_key, 0))
            matched = False
            for i in range(len(intervals)):
                start, end, title = intervals[i]
                if start <= t < end:
                    if i != current_interval_idx and current_group:
                        chunks.append(
                            self._create_chunk_from_records(
                                current_group,
                                {
                                    **doc.metadata,
                                    "chapter_title": intervals[current_interval_idx][2],
                                },
                                f"{doc_id}_ch{current_interval_idx}",
                            )
                        )
                        current_group = []

                    current_interval_idx = i
                    current_group.append(record)
                    matched = True
                    break

            if not matched and current_group:
                current_group.append(record)

        if current_group:
            chunks.append(
                self._create_chunk_from_records(
                    current_group,
                    {
                        **doc.metadata,
                        "chapter_title": intervals[current_interval_idx][2],
                    },
                    f"{doc_id}_ch{current_interval_idx}",
                )
            )

        return chunks

    def _create_chunk_from_records(
        self, records: List[Dict], meta: Dict, chunk_id: str
    ) -> SayouChunk:
        """
        Helper: Merges a list of records into a single text chunk.
        """
        merged_text = " ".join([r.get("text", "") for r in records]).strip()
        start_time = records[0].get("start") if records else 0
        end_time = (
            records[-1].get("start", 0) + records[-1].get("duration", 0)
            if records
            else 0
        )

        new_meta = meta.copy()
        new_meta.update(
            {
                "chunk_id": chunk_id,
                "record_count": len(records),
                "sayou:startTime": start_time,
                "sayou:endTime": end_time,
                "sayou:duration": end_time - start_time,
            }
        )

        return SayouChunk(content=merged_text, metadata=new_meta)

    # --------------------------------------------------------------------------
    # Mode 1: Text Splitting Logic (Preserved)
    # --------------------------------------------------------------------------
    def _split_text(self, doc: SayouBlock) -> List[SayouChunk]:
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
