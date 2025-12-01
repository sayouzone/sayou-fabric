from abc import abstractmethod
from typing import List

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time

from ..core.exceptions import ProcessingError
from ..core.schemas import ContentBlock


class BaseProcessor(BaseComponent):
    """
    (Tier 1) Abstract base class for processing/cleaning ContentBlocks.

    Processors operate on data that is already normalized. They can modify content
    (e.g., PII masking, Imputation) or filter out blocks (e.g., Deduplication).
    """

    component_name = "BaseProcessor"

    @measure_time
    def process(self, blocks: List[ContentBlock]) -> List[ContentBlock]:
        """
        Execute the processing logic on a list of blocks.

        Args:
            blocks: Input list of ContentBlocks.

        Returns:
            List[ContentBlock]: Processed list of ContentBlocks.

        Raises:
            ProcessingError: If processing logic fails.
        """
        try:
            if not blocks:
                return []

            return self._do_process(blocks)

        except Exception as e:
            wrapped_error = ProcessingError(f"[{self.component_name}] Failed: {str(e)}")
            self.logger.error(wrapped_error, exc_info=True)
            raise wrapped_error

    @abstractmethod
    def _do_process(self, blocks: List[ContentBlock]) -> List[ContentBlock]:
        """
        [Abstract Hook] Implement cleaning/filtering logic.

        Args:
            blocks: List of input ContentBlocks.

        Returns:
            List[ContentBlock]: Modified list of ContentBlocks.
        """
        raise NotImplementedError
