from typing import List, Dict, Any, Set

from sayou.core.base_component import BaseComponent

from .interfaces.base_splitter import BaseSplitter
from .core.exceptions import ChunkingError

class ChunkingPipeline(BaseComponent):
    """
    (Orchestrator) 'Chunking' 파이프라인 (스마트 라우터).
    'split' 단일 동사로 모든 청킹 요청을 라우팅합니다.
    """
    component_name = "ChunkingPipeline"

    def __init__(self, splitters: List[BaseSplitter] = None):
        """
        Args:
            splitters (List[BaseSplitter]): 
                등록할 모든 T2(기본) 및 T3(플러그인) 스플리터 인스턴스 리스트.
        """
        self.handler_map: Dict[str, BaseSplitter] = {}
        
        # ⭐️ 'Splitter' 코덱 등록 (T3가 T2를 덮어쓸 수 있음)
        self._build_dispatch_map(splitters or [])
        
        self._log(f"Pipeline initialized with {len(self.handler_map)} split types:")
        for type_name, handler in self.handler_map.items():
            self._log(f"  - '{type_name}' handled by {handler.component_name}")

    def _build_dispatch_map(self, plugins: List[BaseSplitter]):
        """플러그인의 'SUPPORTED_TYPES'를 읽어 맵에 등록"""
        for plugin in plugins:
            if not isinstance(plugin, BaseSplitter):
                self._log(f"Warning: Item {plugin} is not valid BaseSplitter. Skipping.")
                continue
                
            for split_type in plugin.SUPPORTED_TYPES:
                if split_type in self.handler_map:
                    old = self.handler_map[split_type].component_name
                    self._log(f"Warning: Duplicate handler for '{split_type}'. "
                            f"Overwriting '{old}' with '{plugin.component_name}'.")
                self.handler_map[split_type] = plugin

    def initialize(self, **kwargs):
        """등록된 모든 플러그인에 설정을 주입합니다."""
        initialized_plugins: Set[BaseSplitter] = set(self.handler_map.values())
        for plugin in initialized_plugins:
            try:
                plugin.initialize(**kwargs)
            except Exception as e:
                self._log(f"Failed to initialize {plugin.component_name}: {e}")

    def _get_handler(self, query: Dict[str, Any]) -> BaseSplitter:
        """[공통] 쿼리 타입에 맞는 핸들러(플러그인)를 찾는 공통 로직"""
        query_type = query.get("type")
        if not query_type:
            raise ChunkingError("Split request must have a 'type' field.")
        
        handler = self.handler_map.get(query_type)
        if not handler:
            raise ChunkingError(f"No handler registered for split type: '{query_type}'")
        return handler

    def split(self, request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        '문서 분할'을 실행합니다.
        요청 'type'에 맞는 핸들러를 찾아 'split' 메서드를 호출합니다.
        """
        handler = self._get_handler(request)
        return handler.split(request)