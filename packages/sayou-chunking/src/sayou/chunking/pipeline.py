from typing import List, Dict, Any, Optional
from sayou.core.base_component import BaseComponent

from .core.exceptions import ChunkingError
from .interfaces.base_splitter import BaseSplitter
from .splitter.recursive import RecursiveSplitter
from .splitter.fixed_length import FixedLengthSplitter
from .splitter.structure import StructureSplitter
from .splitter.semantic import SemanticSplitter
from .splitter.parent_document import ParentDocumentSplitter
from .plugins.markdown_plugin import MarkdownPlugin

class ChunkingPipeline(BaseComponent):
    component_name = "ChunkingPipeline"

    def __init__(
        self,
        extra_splitters: Optional[List[BaseSplitter]] = None
    ):
        self.handler_map: Dict[str, BaseSplitter] = {}
        
        default_splitters = [
            RecursiveSplitter(),
            FixedLengthSplitter(),
            StructureSplitter(),
            SemanticSplitter(),
            ParentDocumentSplitter(),
            MarkdownPlugin()
        ]
        
        self._register(default_splitters)
        if extra_splitters:
            self._register(extra_splitters)

    def _register(self, splitters: List[BaseSplitter]):
        for s in splitters:
            for t in s.SUPPORTED_TYPES:
                self.handler_map[t] = s

    def initialize(self, **kwargs):
        for handler in set(self.handler_map.values()):
            handler.initialize(**kwargs)

    def run(self, request: Dict[str, Any]) -> List[Dict[str, Any]]:
        req_type = request.get("type")
        handler = self.handler_map.get(req_type)
        
        if not handler:
            raise ChunkingError(f"Unknown split type: '{req_type}'. Available: {list(self.handler_map.keys())}")
            
        return handler.split(request)