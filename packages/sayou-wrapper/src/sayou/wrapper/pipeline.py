from typing import Any, Dict, List, Optional

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import safe_run

from .adapter.document_chunk_adapter import DocumentChunkAdapter
from .core.exceptions import AdaptationError
from .core.schemas import WrapperOutput
from .interfaces.base_adapter import BaseAdapter


class WrapperPipeline(BaseComponent):
    component_name = "WrapperPipeline"

    def __init__(self, extra_adapters: Optional[List[BaseAdapter]] = None):
        super().__init__()
        self.adapters: Dict[str, BaseAdapter] = {}

        defaults = [DocumentChunkAdapter()]
        self._register(defaults)

        if extra_adapters:
            self._register(extra_adapters)

    def _register(self, adapters: List[BaseAdapter]):
        for a in adapters:
            for t in getattr(a, "SUPPORTED_TYPES", []):
                self.adapters[t] = a

    @safe_run(default_return=None)
    def initialize(self, **kwargs):
        for adapter in set(self.adapters.values()):
            if hasattr(adapter, "initialize"):
                adapter.initialize(**kwargs)
        self._log(
            f"WrapperPipeline initialized. Strategies: {list(self.adapters.keys())}"
        )

    def run(self, input_data: Any, strategy: str = "default") -> WrapperOutput:
        """
        Run the wrapper pipeline.

        Args:
            input_data: List of Chunks or Dicts.
            strategy: 'document_chunk' or 'default'.
        """
        adapter = self.adapters.get(strategy)
        if not adapter:
            raise AdaptationError(
                f"Unknown strategy '{strategy}'. Available: {list(self.adapters.keys())}"
            )

        self._log(f"Wrapping using strategy: {strategy}")
        return adapter.adapt(input_data)
