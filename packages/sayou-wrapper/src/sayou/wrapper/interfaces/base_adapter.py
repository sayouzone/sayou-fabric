from abc import abstractmethod
from typing import Any, List

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time

from ..core.exceptions import AdaptationError
from ..core.schemas import WrapperOutput


class BaseAdapter(BaseComponent):
    """
    (Tier 1) Abstract base class for converting external data into Sayou Standard Schema.
    """

    component_name = "BaseAdapter"
    SUPPORTED_TYPES: List[str] = []

    @measure_time
    def adapt(self, input_data: Any) -> WrapperOutput:
        """
        Execute the adaptation process.

        Args:
            input_data (Any): Can be List[Chunk], List[Dict], or raw data object.

        Returns:
            WrapperOutput: Container holding standardized SayouNodes.

        Raises:
            AdaptationError: If adaptation fails.
        """
        self._log(f"Adapting data (Type: {type(input_data).__name__})")

        try:
            output = self._do_adapt(input_data)

            self._log(f"Adaptation complete. Generated {len(output.nodes)} nodes.")
            return output

        except Exception as e:
            wrapped_error = AdaptationError(f"[{self.component_name}] Failed: {str(e)}")
            self.logger.error(wrapped_error, exc_info=True)
            raise wrapped_error

    @abstractmethod
    def _do_adapt(self, input_data: Any) -> WrapperOutput:
        """
        [Abstract Hook] Implement the mapping logic.
        """
        raise NotImplementedError
