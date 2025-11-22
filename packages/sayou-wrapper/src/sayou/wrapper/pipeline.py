from typing import Any, Dict, List, Optional

from sayou.core.base_component import BaseComponent

from .core.exceptions import WrapperError
from .interfaces.base_adapter import BaseAdapter
from .adapter.document_adapter import DocumentChunkAdapter

class WrapperPipeline(BaseComponent):
    component_name = "WrapperPipeline"

    def __init__(
        self,
        extra_adapters: Optional[List[BaseAdapter]] = None
    ):
        self.handler_map: Dict[str, BaseAdapter] = {}

        default_adapters = [
            DocumentChunkAdapter(),
        ]

        self._register(default_adapters)
        if extra_adapters:
            self._register(extra_adapters)

    def _register(self, adapters: List[BaseAdapter]):
        for adapter in adapters:
            for t in getattr(adapter, "SUPPORTED_TYPES", []):
                self.handler_map[t] = adapter

    def initialize(self, **kwargs):
        for handler in set(self.handler_map.values()):
            handler.initialize(**kwargs)

    def run(self, raw_data: Any, adapter_type: str = "document_chunk") -> Dict[str, Any]:
        handler = self.handler_map.get(adapter_type)
        
        if not handler:
            raise WrapperError(f"Unknown adapter type: '{adapter_type}'. Available: {list(self.handler_map.keys())}")
            
        self._log(f"Routing to {handler.component_name}...")
        try:
            return handler.adapt(raw_data)
        except Exception as e:
            self._log(f"Pipeline Error: {e}")
            raise WrapperError(e)