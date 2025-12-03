from abc import abstractmethod
from typing import Any, Dict, Union

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time
from sayou.core.schemas import SayouOutput

from ..core.exceptions import BuildError


class BaseBuilder(BaseComponent):
    """
    (Tier 1) Abstract base class for assembling SayouNodes into target formats.
    """

    component_name = "BaseBuilder"
    SUPPORTED_TYPES = []

    @measure_time
    def build(self, input_data: Union[SayouOutput, Dict]) -> Any:
        """
        Execute the building process.

        Args:
            input_data (Union[SayouOutput, Dict]): Standardized node data.

        Returns:
            Any: The assembled payload (Dict, List, Str) ready for Loader.

        Raises:
            BuildError: If the building process fails.
        """
        self._log(f"Building data with {self.component_name}")

        # Input Normalization
        if isinstance(input_data, dict):
            try:
                # 딕셔너리가 들어오면 Pydantic 모델로 변환하여 검증
                sayou_output = SayouOutput(**input_data)
            except Exception as e:
                raise BuildError(f"Invalid input format: {e}")
        elif isinstance(input_data, SayouOutput):
            sayou_output = input_data
        else:
            raise BuildError(f"Unsupported input type: {type(input_data)}")

        try:
            return self._do_build(sayou_output)
        except Exception as e:
            wrapped_error = BuildError(f"[{self.component_name}] Failed: {str(e)}")
            self.logger.error(wrapped_error, exc_info=True)
            raise wrapped_error

    @abstractmethod
    def _do_build(self, data: SayouOutput) -> Any:
        """
        [Abstract Hook] Implement the transformation logic.
        """
        raise NotImplementedError
