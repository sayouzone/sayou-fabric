from typing import List

from ..core.schemas import Chunk, InputDocument
from ..interfaces.base_splitter import BaseSplitter


class AgenticSplitter(BaseSplitter):
    """
    LLM-based Splitter (Placeholder).

    Intended to use an LLM Agent to determine the most semantically
    meaningful breakpoints in the text.
    """

    component_name = "AgenticSplitter"
    SUPPORTED_TYPES = ["llm_agent"]

    def _do_split(self, doc: InputDocument) -> List[Chunk]:
        """
        Delegate splitting logic to an LLM (Mock implementation).
        """
        # TODO: 실제 LLM Client 연동 필요
        self._log(
            "Agentic splitting is not fully implemented yet. Returning raw content."
        )

        return [Chunk(chunk_content=doc.content, metadata=doc.metadata)]
