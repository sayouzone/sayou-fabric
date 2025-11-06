from sayou.core.base_component import BaseComponent
from sayou.rag.interfaces import BaseRouter, BaseTransformer, BaseTracer, BaseFetcher, BaseGenerator
from typing import Dict, Any, List, Optional

class RAGExecutor(BaseComponent):
    """
    RAG 워크플로우(그래프) 실행기.
    T2/T3 컴포넌트(노드)들을 주입받아
    정의된 순서(그래프)대로 실행합니다.
    """
    component_name = "RAGExecutor"

    def __init__(self, 
        generator: BaseGenerator,
        fetcher: BaseFetcher,
        # ⭐️ (선택적) 이 노드들은 없을 수도 있음
        router: Optional[BaseRouter] = None,
        transformer: Optional[BaseTransformer] = None,
        tracer: Optional[BaseTracer] = None
    ):
        
        # (필수 노드)
        self.generator = generator
        self.fetcher = fetcher
        
        # (선택적 노드)
        self.router = router
        self.transformer = transformer
        self.tracer = tracer
        
        self._log("RAGExecutor initialized with configured nodes.")

    def run(self, query: str, chat_history: List = None) -> Dict[str, Any]:
        """
        주입된 컴포넌트(노드)들을 기반으로 워크플로우를 동적으로 실행합니다.
        """
        chat_history = chat_history or []
        context = {} # (수집된 컨텍스트 저장)
        
        # 1. (선택) 라우팅 (Router)
        route_result = {"domain": "default"}
        if self.router:
            route_result = self.router.route(query, chat_history)
            context["route"] = route_result
        
        # 2. (선택) 위치 추적 (Tracer)
        trace_result = {"source_type": "default_vector_index"}
        if self.tracer:
            # ⭐️ Tracer는 Router의 결과를 입력으로 받음
            trace_result = self.tracer.trace(route_result)
            context["trace"] = trace_result
            
        # 3. (선택) 쿼리 변환 (Transformer)
        queries = [query] # (원본 쿼리 기본값)
        if self.transformer:
            queries = self.transformer.transform(query, chat_history)
            context["transformed_queries"] = queries
            
        # 4. (필수) 데이터 검색 (Fetcher)
        # ⭐️ Fetcher는 Tracer와 Transformer의 결과를 입력으로 받음
        documents = self.fetcher.fetch(queries, trace_result)
        context["documents"] = documents
        
        # 5. (필수) 답변 생성 (Generator)
        # ⭐️ Generator는 원본 쿼리와 Fetcher의 결과를 입력으로 받음
        final_response = self.generator.generate(query, documents, chat_history)
        
        return {
            "answer": final_response.get("answer"),
            "context": context, # (디버깅/추적을 위한 전체 컨텍스트)
            "metadata": final_response.get("metadata")
        }