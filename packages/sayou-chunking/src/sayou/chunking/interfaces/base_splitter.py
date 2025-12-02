from abc import abstractmethod
from typing import Any, Dict, List, Union

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time

from ..core.exceptions import ChunkingError
from ..core.schemas import Chunk, InputDocument


class BaseSplitter(BaseComponent):
    """
    (Tier 1) Abstract base class for splitting text into chunks.
    """

    component_name = "BaseSplitter"
    SUPPORTED_TYPES: List[str] = []

    @measure_time
    def split(self, input_data: Union[Dict[str, Any], InputDocument]) -> List[Chunk]:
        # 1. Input Normalization
        doc = self._normalize_input(input_data)

        # 2. Config Merge (Input metadata overrides defaults)
        # (Template 구현체에서 self.chunk_size 등을 쓰겠지만, 여기선 doc에 병합해둠)
        split_config = (
            input_data.get("config", {}) if isinstance(input_data, dict) else {}
        )
        if split_config:
            doc.metadata["config"] = {**doc.metadata.get("config", {}), **split_config}

        try:
            return self._do_split(doc)
        except Exception as e:
            self.logger.error(f"Split failed: {e}", exc_info=True)
            raise ChunkingError(f"[{self.component_name}] {e}")

    @abstractmethod
    def _do_split(self, doc: InputDocument) -> List[Chunk]:
        raise NotImplementedError

    def _normalize_input(self, input_data: Any) -> InputDocument:
        if isinstance(input_data, InputDocument):
            return input_data

        content = (
            getattr(input_data, "content", None)
            or input_data.get("content")
            or input_data.get("chunk_content")
        )
        metadata = getattr(input_data, "metadata", None) or input_data.get(
            "metadata", {}
        )

        if content is None:
            raise ChunkingError("Input must have content.")

        return InputDocument(content=str(content), metadata=metadata)