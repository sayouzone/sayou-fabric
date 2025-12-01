from abc import abstractmethod
from typing import Any, List

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time

from ..core.exceptions import NormalizationError
from ..core.schemas import ContentBlock


class BaseNormalizer(BaseComponent):
    """
    (Tier 1) Abstract base class for converting raw input into ContentBlocks.

    Normalizers are responsible for structural transformation:
    Raw Data (JSON, HTML, DB Row) -> List[ContentBlock]
    """

    component_name = "BaseNormalizer"
    SUPPORTED_TYPES = []

    @measure_time
    def normalize(self, raw_data: Any) -> List[ContentBlock]:
        """
        Execute the normalization process.

        Args:
            raw_data: The raw input data from Connector or Document.

        Returns:
            List[ContentBlock]: A list of normalized content blocks.

        Raises:
            NormalizationError: If transformation fails.
        """
        self._log(f"Normalizing data (Type: {type(raw_data).__name__})")
        try:
            blocks = self._do_normalize(raw_data)
            if not isinstance(blocks, list):
                raise NormalizationError(f"Output must be a list, got {type(blocks)}")

            return blocks

        except Exception as e:
            wrapped_error = NormalizationError(
                f"[{self.component_name}] Failed: {str(e)}"
            )
            self.logger.error(wrapped_error, exc_info=True)
            raise wrapped_error

    @abstractmethod
    def _do_normalize(self, raw_data: Any) -> List[ContentBlock]:
        """
        [Abstract Hook] Implement logic to convert specific raw format to ContentBlocks.

        Args:
            raw_data: The raw input.

        Returns:
            List[ContentBlock]: The standardized blocks.
        """
        raise NotImplementedError
