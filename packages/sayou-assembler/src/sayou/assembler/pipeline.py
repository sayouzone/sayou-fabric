from typing import Any, Dict, List, Optional

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import safe_run

from .builder.graph_builder import GraphBuilder
from .builder.vector_builder import VectorBuilder
from .core.exceptions import BuildError
from .interfaces.base_builder import BaseBuilder


class AssemblerPipeline(BaseComponent):
    component_name = "AssemblerPipeline"

    def __init__(self, extra_builders: Optional[List[BaseBuilder]] = None):
        super().__init__()
        self.builders: Dict[str, BaseBuilder] = {}

        defaults = [GraphBuilder(), VectorBuilder()]
        self._register(defaults)

        if extra_builders:
            self._register(extra_builders)

    def _register(self, builders: List[BaseBuilder]):
        for b in builders:
            for t in getattr(b, "SUPPORTED_TYPES", []):
                self.builders[t] = b

    @safe_run(default_return=None)
    def initialize(self, **kwargs):
        for b in set(self.builders.values()):
            if hasattr(b, "initialize"):
                b.initialize(**kwargs)
        self._log(
            f"AssemblerPipeline initialized. Strategies: {list(self.builders.keys())}"
        )

    def run(self, input_data: Any, strategy: str = "graph") -> Any:
        builder = self.builders.get(strategy)
        if not builder:
            raise BuildError(
                f"Unknown strategy '{strategy}'. Available: {list(self.builders.keys())}"
            )

        self._log(f"Assembling using strategy: {strategy}")
        return builder.build(input_data)
