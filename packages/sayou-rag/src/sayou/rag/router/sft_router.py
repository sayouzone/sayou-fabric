from sayou.rag.interfaces.base_router import BaseRouter
from sayou.rag.core.exceptions import RAGError
from sayou.llm.interfaces.base_llm_client import BaseLLMClient # (가상: sayou-llm 라이브러리)
from typing import Dict, Any, List
import json

class SayouSftRouter(BaseRouter):
    """
    (Tier 2 - 기본 전략) SFT(Small Fine-Tuned) LLM을 사용하여
    사용자 쿼리의 '도메인'을 분류합니다.
    """
    component_name = "SayouSftRouter"
    
    def initialize(self, **kwargs):
        """SFT 모델을 호출할 LLM 클라이언트를 주입받습니다."""
        self.sft_client: BaseLLMClient = kwargs.get("sft_router_client")
        if not self.sft_client:
            raise RAGError("SayouSftRouter requires 'sft_router_client'.")
        self._log("SayouSftRouter (Default) initialized.")

    def _do_route(self, query: str, chat_history: List) -> Dict[str, Any]:
        """[T1 구현] SFT 클라이언트를 호출하여 도메인을 추출합니다."""
        
        # (실제로는 chat_history도 포함하는 복잡한 프롬프트)
        prompt = f"""
        주어진 쿼리를 다음 도메인 중 하나로 분류하고 JSON을 반환해:
        ["user_profile", "order_history", "general_knowledge"]
        Query: {query}
        """
        
        # ⭐️ 외부 도구(LLM) 호출
        raw_response = self.sft_client.invoke(prompt) 
        
        try:
            # (e.g., raw_response = '{"domain": "user_profile", "confidence": 0.9}')
            result = json.loads(raw_response.get("text", "{}"))
            return {
                "domain": result.get("domain", "general_knowledge"),
                "confidence": result.get("confidence", 0.5)
            }
        except json.JSONDecodeError:
            return {"domain": "general_knowledge", "confidence": 0.1} # (파싱 실패)