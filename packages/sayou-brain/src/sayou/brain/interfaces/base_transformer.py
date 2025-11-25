from abc import abstractmethod
from typing import List

from sayou.core.base_component import BaseComponent

from ..core.exceptions import BrainError

class BaseTransformer(BaseComponent):
    component_name = "BaseTransformer"

    def transform(self, query: str, chat_history: List = None) -> List[str]:
        """[공통 골격] 쿼리 변환을 실행하고 결과를 표준화합니다."""
        self._log(f"Transforming query: '{query[:30]}...'")
        try:
            transformed_queries = self._do_transform(query, chat_history or [])
            
            if not isinstance(transformed_queries, list):
                raise BrainError("Transform result must be a list of strings.")
                
            self._log(f"Transformed into {len(transformed_queries)} sub-queries.")
            return transformed_queries
        except Exception as e:
            raise BrainError(f"Query transformation failed: {e}")

    @abstractmethod
    def _do_transform(self, query: str, chat_history: List) -> List[str]:
        """[T2 구현 필수] (e.g., LLM 호출로 가상 문서 생성)
        (결과 포맷: ["변환된 쿼리 1", "변환된 쿼리 2"])
        """
        raise NotImplementedError