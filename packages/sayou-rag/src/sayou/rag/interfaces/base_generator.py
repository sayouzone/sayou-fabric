from abc import abstractmethod
from typing import Dict, Any, List
from sayou.core.base_component import BaseComponent
from sayou.rag.core.exceptions import RAGError

class BaseGenerator(BaseComponent):
    component_name = "BaseGenerator"

    def generate(self, query: str, context: List[Dict[str, Any]], chat_history: List = None) -> Dict[str, Any]:
        """[공통 골격] 컨텍스트와 쿼리를 기반으로 최종 답변을 생성합니다."""
        self._log(f"Generating answer for query: '{query[:30]}...' with {len(context)} contexts.")
        try:
            answer_result = self._do_generate(query, context, chat_history or [])
            if "answer" not in answer_result:
                    raise RAGError("Generate result must contain 'answer'.")

            return answer_result
        except Exception as e:
            raise RAGError(f"Answer generation failed: {e}")

    @abstractmethod
    def _do_generate(self, query: str, context: List[Dict[str, Any]], chat_history: List) -> Dict[str, Any]:
        """[T2 구현 필수] (e.g., 프롬프트 엔지니어링 및 LLM 호출)
        (결과 포맷: {"answer": "최종 답변...", "metadata": {"token_usage": ...}})
        """
        raise NotImplementedError