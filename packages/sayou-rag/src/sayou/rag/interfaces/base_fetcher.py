from abc import abstractmethod
from typing import Dict, Any, List
from sayou.core.base_component import BaseComponent
from sayou.rag.core.exceptions import RAGError

class BaseFetcher(BaseComponent):
    component_name = "BaseFetcher"

    def fetch(self, queries: List[str], trace_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """[공통 골격] 변환된 쿼리(들)와 위치 정보를 사용해 문서를 검색합니다."""
        self._log(f"Fetching data from '{trace_result.get('source_type')}' using {len(queries)} queries.")
        try:
            # ⭐️ (T3 플러그인 - Reranker가 여기서 작동할 수 있음)
            documents = self._do_fetch(queries, trace_result)
            
            self._log(f"Fetched {len(documents)} documents.")
            # (여기서 documents 형식을 표준 Dict[Document]로 검증/변환)
            return documents
        except Exception as e:
            raise RAGError(f"Data fetching failed: {e}")

    @abstractmethod
    def _do_fetch(self, queries: List[str], trace_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """[T2 구현 필수] (e.g., Extractor.search() 또는 .query() 호출)
        (결과 포맷: [{"chunk_content": "...", "metadata": ...}, ...])
        """
        raise NotImplementedError