from typing import Any, Dict, List, Optional

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import safe_run

from .core.exceptions import SplitterError
from .core.schemas import Chunk
from .interfaces.base_splitter import BaseSplitter
from .plugins.markdown_splitter import MarkdownSplitter
from .splitter.fixed_length_splitter import FixedLengthSplitter
from .splitter.parent_document_splitter import ParentDocumentSplitter
from .splitter.recursive_splitter import RecursiveSplitter
from .splitter.semantic_splitter import SemanticSplitter
from .splitter.structure_splitter import StructureSplitter


class ChunkingPipeline(BaseComponent):
    component_name = "ChunkingPipeline"

    def __init__(self, extra_splitters: Optional[List[BaseSplitter]] = None):
        super().__init__()
        self.splitters: Dict[str, BaseSplitter] = {}

        default_splitters = [
            RecursiveSplitter(),
            FixedLengthSplitter(),
            StructureSplitter(),
            SemanticSplitter(),
            ParentDocumentSplitter(),
            MarkdownSplitter(),
        ]

        self._register(default_splitters)
        if extra_splitters:
            self._register(extra_splitters)

    def _register(self, splitters: List[BaseSplitter]):
        for s in splitters:
            for t in getattr(s, "SUPPORTED_TYPES", []):
                self.splitters[t] = s

    @safe_run(default_return=None)
    def initialize(self, **kwargs):
        for s in set(self.splitters.values()):
            s.initialize(**kwargs)
        self._log(
            f"ChunkingPipeline initialized. Strategies: {list(self.splitters.keys())}"
        )

    def run(self, input_data: Any, strategy: str = "default") -> List[Chunk]:
        splitter = self.splitters.get(strategy)
        if not splitter:
            raise SplitterError(
                f"Unknown strategy '{strategy}'. Available: {list(self.splitters.keys())}"
            )

        return splitter.split(input_data)
