from sayou.core.base_component import BaseComponent
from .interfaces.base_llm_client import BaseLLMClient

class LLMPipeline(BaseComponent):
    """
    LLM 클라이언트를 감싸는 단순 파이프라인.
    RAG 로직을 모르며, 오직 텍스트 생성만 담당합니다.
    """
    component_name = "LLMPipeline"

    def __init__(self, client: BaseLLMClient):
        self.client = client
        self._log(f"Pipeline initialized with client: {client.component_name}")

    def initialize(self, **kwargs):
        """LLM 클라이언트를 초기화합니다."""
        self.client.initialize(**kwargs)

    def run(self, query: str, context: str = None, **kwargs) -> dict:
        """
        [개선됨] query와 (선택적) context를 받아 텍스트를 생성합니다.
        
        :param query: 사용자 질문
        :param context: (RAG용) 주입될 문맥
        :return: {"answer": "LLM 답변"}
        """
        self._log("Generating text...")
        
        # RAG 지휘자가 context를 주입하면 프롬프트를 재구성
        if context:
            # (이 부분은 BaseLLMClient의 구현에 따라 달라질 수 있습니다)
            # 여기서는 간단히 문자열 합치기로 가정합니다.
            prompt = f"Context: {context}\n\nQuery: {query}\n\nAnswer:"
        else:
            prompt = query

        # client.generate()가 문자열을 반환한다고 가정
        answer = self.client.invoke(prompt)
        
        return {"answer": answer}