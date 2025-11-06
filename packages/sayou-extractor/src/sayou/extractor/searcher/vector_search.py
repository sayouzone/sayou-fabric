from abc import abstractmethod
from typing import Any, Dict, List
from sayou.extractor.interfaces.base_searcher import BaseSearcher
from sayou.extractor.core.exceptions import SearchError

class VectorSearchTemplate(BaseSearcher):
    """
    (Tier 2) '벡터 유사도 검색'을 위한 '추상 템플릿'.
    Tier 3(e.g., FAISS, PGVector) 플러그인이 이 템플릿을 상속받아
    '실제 드라이버' 로직을 구현합니다.
    """
    component_name = "VectorSearchTemplate"
    SUPPORTED_TYPES = ["vector_knn"] # 👈 "vector_knn" 처리
    
    # (DB/인덱스 커넥션은 Tier 3가 initialize()에서 구현)

    def _do_search(self, search_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """[Tier 1 구현] 쿼리 검증 후, Tier 3의 실행 로직 호출"""
        
        vector = search_request.get("vector")
        top_k = search_request.get("top_k", 5)
        
        if not vector or not isinstance(vector, list):
            raise SearchError("'vector_knn' request requires a 'vector' field (list of floats).")
            
        # ⭐️ Tier 3 플러그인이 '실제' 검색 로직을 구현
        # (결과 포맷: [{"chunk_id": "...", "score": 0.9, "metadata": {...}}, ...])
        return self._execute_knn_search(vector, top_k)

    @abstractmethod
    def _execute_knn_search(self, vector: List[float], top_k: int) -> List[Dict[str, Any]]:
        """
        [Tier 3 구현 필수] 실제 DB/Index 드라이버를 사용하여
        K-NN 검색을 실행하고 (청크ID, 점수) 리스트를 반환합니다.
        """
        raise NotImplementedError