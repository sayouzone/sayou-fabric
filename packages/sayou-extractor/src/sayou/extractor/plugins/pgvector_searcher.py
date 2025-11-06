from typing import Any, Dict, List
from sayou.extractor.searcher.vector_search import VectorSearchTemplate
from sayou.extractor.querier.sql import SqlQuerier
from sayou.extractor.core.exceptions import ExtractorError

class PGVectorSearcher(VectorSearchTemplate):
    """
    (Tier 3) 'PostgreSQL (pgvector)'을 사용한 벡터 검색 특화 어댑터.
    Tier 2(VectorSearchTemplate)를 상속받고,
    Tier 2(SqlQuerier)를 '내부적으로 사용'합니다.
    """
    component_name = "PGVectorSearcher"

    def initialize(self, **kwargs):
        # 1. 'SQL 쿼리어' 엔진을 내부적으로 초기화
        # (PGVector는 결국 SQL로 실행되기 때문)
        try:
            self.sql_querier = SqlQuerier()
            self.sql_querier.initialize(**kwargs) # 👈 db_uri 전달
        except ExtractorError as e:
            raise ExtractorError(f"PGVectorSearcher failed to initialize SqlQuerier: {e}")
            
        self.table_name = kwargs.get("vector_table_name", "documents")
        self.embedding_column = kwargs.get("embedding_column", "embedding")
        self._log("PGVectorSearcher initialized.")

    def _execute_knn_search(self, vector: List[float], top_k: int) -> List[Dict[str, Any]]:
        """[Tier 2 구현] pgvector의 '<->' 연산자를 사용하는 SQL 쿼리 생성"""
        
        # (SQL Injection 방지를 위해 실제로는 파라미터 바인딩 사용)
        vector_str = str(vector) # (실제로는 f"'{vector}'" 등 포맷팅 필요)
        
        sql_statement = f"""
            SELECT 
                chunk_id, 
                metadata,
                1 - ({self.embedding_column} <-> '{vector_str}') AS similarity_score
            FROM {self.table_name}
            ORDER BY similarity_score DESC
            LIMIT {top_k}
        """
        
        query = {
            "type": "sql",
            "statement": sql_statement
            # "params": {"query_vector": vector_str, "top_k": top_k} # (권장)
        }
        
        # 2. ⭐️ 내부의 'SqlQuerier' (Tier 2) 툴킷을 호출
        return self.sql_querier._do_query(query)