from sayou.rag.interfaces.base_fetcher import BaseFetcher
from sayou.rag.core.exceptions import RAGError
from sayou.extractor.pipeline import ExtractorPipeline
from typing import Dict, Any, List

class SayouVectorFetcher(BaseFetcher):
    """
    (Tier 2 - 기본 전략) sayou-extractor를 사용하여
    Vector DB (e.g., pgvector)에서 문서를 검색합니다.
    """
    component_name = "SayouVectorFetcher"

    def initialize(self, **kwargs):
        """Vector DB를 쿼리할 'extractor' 파이프라인을 주입받습니다."""
        self.extractor: ExtractorPipeline = kwargs.get("extractor_pipeline")
        if not self.extractor:
            raise RAGError("SayouVectorFetcher requires 'extractor_pipeline'.")
        self._log("SayouVectorFetcher (Default) initialized.")
        
        # (T2가 자체적으로 임베딩 모델을 가질 수도 있음)
        # self.embedding_model = kwargs.get("embedding_model")

    def _do_fetch(self, queries: List[str], trace_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """[T1 구현] Extractor.search()를 호출합니다."""
        
        # T2 기본 전략: 변환된 쿼리 중 첫 번째 것만 사용
        query_text = queries[0] 
        
        # (실제로는 여기서 query_text를 임베딩해야 함)
        query_vector = [0.1, 0.2, ...] # self.embedding_model.embed(query_text)
        
        index_name = trace_result.get("index_name", "default_documents")
        
        # ⭐️ 외부 도구(Extractor) 호출
        try:
            search_request = {
                "type": "vector_knn", # (Extractor가 지원하는 타입)
                "vector": query_vector,
                "top_k": 3,
                "target_index": index_name # (DB 테이블명 등)
            }
            documents = self.extractor.search(search_request)
            return documents
        
        except Exception as e:
            raise RAGError(f"Vector fetching failed: {e}")