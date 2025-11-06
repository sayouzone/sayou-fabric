from sayou.rag.interfaces.base_generator import BaseGenerator
from sayou.llm.interfaces.base_llm_client import BaseLLMClient # 👈 '도구' 타입
from typing import Dict, Any, List

class SayouLLMGenerator(BaseGenerator):
    """
    (T2) sayou-llm 클라이언트를 사용해 최종 답변을 생성.
    '도구'를 생성자에서 직접 주입받습니다.
    """
    component_name = "SayouLLMGenerator"

    def __init__(self, llm_client: BaseLLMClient):
        """
        Args:
            llm_client (BaseLLMClient): 
                답변 생성에 사용할 sayou-llm의 T1 인터페이스 호환 클라이언트.
        """
        self.llm_client = llm_client
        self._log("SayouLLMGenerator (Default) initialized.")

    def _do_generate(self, query: str, context: List[Dict[str, Any]], chat_history: List) -> Dict[str, Any]:
        prompt = self._build_prompt(query, context)
        
        # ⭐️ 주입받은 도구(LLM) 사용
        response = self.llm_client.invoke(prompt) 
        
        return {
            "answer": response.get("text", "답변 생성에 실패했습니다."),
            "metadata": response.get("metadata", {})
        }

    def _build_prompt(self, query: str, context: List[Dict[str, Any]]) -> str:
        # (프롬프트 엔지니어링 로직...)
        context_str = "\n---\n".join([doc.get("chunk_content", "") for doc in context])
        return f"[Context]\n{context_str}\n\n[Query]\n{query}\n\nAnswer:"