from typing import Any, Dict, List, Optional

from sayou.core.base_component import BaseComponent

from .core.exceptions import AssemblerError
from .interfaces.base_builder import BaseBuilder
from .builder.hierarchy_builder import HierarchyBuilder

class AssemblerPipeline(BaseComponent):
    component_name = "AssemblerPipeline"

    def __init__(
        self,
        extra_builders: Optional[List[BaseBuilder]] = None
    ):
        self.handler_map: Dict[str, BaseBuilder] = {}

        default_builders = [
            HierarchyBuilder(),
            # SemanticBuilder() 
        ]

        self._register(default_builders)
        if extra_builders:
            self._register(extra_builders)

    def _register(self, builders: List[BaseBuilder]):
        for builder in builders:
            for t in getattr(builder, "SUPPORTED_TYPES", []):
                self.handler_map[t] = builder

    def initialize(self, **kwargs):
        for handler in set(self.handler_map.values()):
            handler.initialize(**kwargs)

    def run(self, wrapper_output: Dict[str, Any], strategy: str = "hierarchy") -> Dict[str, Any]:
        handler = self.handler_map.get(strategy)
        
        if not handler:
            raise AssemblerError(f"Unknown strategy: '{strategy}'. Available: {list(self.handler_map.keys())}")
            
        self._log(f"Routing to {handler.component_name}...")
        try:
            return handler.build(wrapper_output)
        except Exception as e:
            self._log(f"Pipeline Error: {e}")
            raise AssemblerError(e)