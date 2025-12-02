from abc import abstractmethod
from typing import Any, Dict, List, Union

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time

from ..core.exceptions import SplitterError
from ..core.schemas import Chunk, InputDocument


class BaseSplitter(BaseComponent):
    """
    (Tier 1) Abstract base class for all chunking strategies.

    Implements the Template Method pattern:
    1. `split()`: Validates input, normalizes it to `InputDocument`, and handles errors.
    2. `_do_split()`: Abstract hook where subclasses implement the algorithm.
    """

    component_name = "BaseSplitter"
    SUPPORTED_TYPES: List[str] = []

    @measure_time
    def split(self, input_data: Union[Dict[str, Any], InputDocument]) -> List[Chunk]:
        """
        [Template Method] Execute the splitting process.

        Args:
            input_data (Union[Dict, InputDocument]): Raw input containing content.

        Returns:
            List[Chunk]: The resulting chunks.
        """
        doc = self._normalize_input(input_data)
        split_config = (
            input_data.get("config", {}) if isinstance(input_data, dict) else {}
        )
        if split_config:
            doc.metadata["config"] = {**doc.metadata.get("config", {}), **split_config}

        try:
            return self._do_split(doc)
        except Exception as e:
            self.logger.error(f"Split failed: {e}", exc_info=True)
            raise SplitterError(f"[{self.component_name}] {e}")

    @abstractmethod
    def _do_split(self, doc: InputDocument) -> List[Chunk]:
        """
        [Abstract Hook] Implement the specific splitting logic.

        Args:
            doc (InputDocument): The normalized input document.

        Returns:
            List[Chunk]: The generated chunks.
        """
        raise NotImplementedError

    def _normalize_input(self, input_data: Any) -> InputDocument:
        """
        Convert various input formats (Dict, ContentBlock) into InputDocument.

        Args:
            input_data (Any): Raw input.

        Returns:
            InputDocument: Normalized object.
        """
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
            raise SplitterError("Input must have content.")

        return InputDocument(content=str(content), metadata=metadata)
