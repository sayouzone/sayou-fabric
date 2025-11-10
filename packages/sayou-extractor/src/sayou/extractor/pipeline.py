from typing import Any, Dict, List
from sayou.core.base_component import BaseComponent
from .interfaces.base_retriever import BaseRetriever
from .interfaces.base_querier import BaseQuerier
from .interfaces.base_searcher import BaseSearcher
from .core.exceptions import QueryError

class ExtractorPipeline(BaseComponent):
    """(Orchestrator) 'Extractor' 파이프라인 (스마트 라우터)."""
    component_name = "ExtractorPipeline"

    def __init__(self, 
        retrievers: List[BaseRetriever] = None,
        queriers: List[BaseQuerier] = None,
        searchers: List[BaseSearcher] = None
    ):
        
        # ⭐️ [수정] 3개의 맵을 '하나의' 범용 맵으로 통일
        self.handler_map: Dict[str, BaseComponent] = {}
        
        # ⭐️ (GOM Player 코덱 등록)
        # 1. Retriever 코덱 등록
        self._build_dispatch_map(retrievers or [])
        # 2. Querier 코덱 등록
        self._build_dispatch_map(queriers or [])
        # 3. Searcher 코덱 등록
        self._build_dispatch_map(searchers or [])
        
        self._log(f"Pipeline initialized with {len(self.handler_map)} query types ({list(self.handler_map.keys())}).")

    def _build_dispatch_map(self, plugins: List[BaseComponent]):
        """
        [수정됨] 모든 플러그인 리스트를 받아 'SUPPORTED_TYPES'를 읽어 맵에 등록
        """
        for plugin in plugins:
            # ⭐️ 어떤 종류의 플러그인이든 'SUPPORTED_TYPES'라는
            # ⭐️ '표준 명찰'을 읽습니다.
            for query_type in plugin.SUPPORTED_TYPES:
                if query_type in self.handler_map:
                    self._log(f"Warning: Duplicate handler for type '{query_type}'. Overwriting.")
                self.handler_map[query_type] = plugin

    def initialize(self, **kwargs):
        """등록된 모든 플러그인에 설정을 주입합니다."""
        # ⭐️ 'set'을 사용해 중복 초기화 방지
        initialized_plugins = set(self.handler_map.values())
        for plugin in initialized_plugins:
            try:
                plugin.initialize(**kwargs)
            except Exception as e:
                self._log(f"Failed to initialize {plugin.component_name}: {e}")

    # --- 실행 메서드 (라우팅) ---

    def _get_handler(self, query: Dict[str, Any]) -> BaseComponent:
        """[신규] 쿼리 타입에 맞는 핸들러(플러그인)를 찾는 공통 로직"""
        query_type = query.get("type")
        if not query_type:
            raise QueryError("Query must have a 'type' field.")
            
        handler = self.handler_map.get(query_type)
        if not handler:
            raise QueryError(f"No handler registered for query type: '{query_type}'")
        return handler

    def retrieve(self, request: Dict[str, Any]) -> Any:
        """'Key-Value' 조회를 실행합니다 (e.g., 파일 읽기)."""
        handler = self._get_handler(request)
        if not isinstance(handler, BaseRetriever):
            raise QueryError(f"Handler for type '{request['type']}' is not a Retriever.")
        return handler.retrieve(request) # 👈 BaseRetriever.retrieve() 호출

    def query(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """'구조화된 쿼리'를 실행합니다 (e.g., SQL)."""
        handler = self._get_handler(query)
        if not isinstance(handler, BaseQuerier):
            raise QueryError(f"Handler for type '{query['type']}' is not a Querier.")
        return handler.query(query) # 👈 BaseQuerier.query() 호출

    def search(self, search_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """'유사도 검색'을 실행합니다 (e.g., Vector)."""
        handler = self._get_handler(search_request)
        if not isinstance(handler, BaseSearcher):
            raise QueryError(f"Handler for type '{search_request['type']}' is not a Searcher.")
        return handler.search(search_request) # 👈 BaseSearcher.search() 호출