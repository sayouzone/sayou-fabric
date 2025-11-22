from typing import Dict, Any, List, Optional

from sayou.core.base_component import BaseComponent

from .doc.markdown import StandardDocRefiner

class RefineryPipeline(BaseComponent):
    component_name = "RefineryPipeline"

    def __init__(
        self,
        extra_refiners: Optional[List[Any]] = None
    ):
        self.handler_map: Dict[str, Any] = {}

        default_refiners = [
            StandardDocRefiner(),
        ]

        self._register(default_refiners)
        if extra_refiners:
            self._register(extra_refiners)

    def _register(self, refiners: List[Any]):
        for refiner in refiners:
            for t in getattr(refiner, "SUPPORTED_TYPES", []):
                self.handler_map[t] = refiner

    def initialize(self, **kwargs):
        for handler in set(self.handler_map.values()):
            handler.initialize(**kwargs)

    def run(self, doc_data: Dict[str, Any], refiner_type: str = "standard_doc") -> List[Any]:
        handler = self.handler_map.get(refiner_type)
        
        if not handler:
            raise ValueError(f"Unknown refiner type: '{refiner_type}'. Available: {list(self.handler_map.keys())}")
            
        self._log(f"Routing to {handler.component_name}...")
        return handler.refine(doc_data)