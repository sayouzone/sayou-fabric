import os
from openai import OpenAI
from sayou.llm.interfaces.base_llm_client import BaseLLMClient, LLMResponse, StreamChunk
from typing import Dict, Any, Iterator, List, Optional
from sayou.llm.core.exceptions import LLMError

class OpenAIClient(BaseLLMClient):
    """
    (Tier 2 - 기본 어댑터) 'OpenAI' API를
    'BaseLLMClient'(T1) 인터페이스 표준에 맞게 구현합니다.
    """
    component_name = "OpenAIClient"
    SUPPORTED_TYPES = ["openai_chat"] # 👈 이 클라이언트가 처리할 타입

    def initialize(self, **kwargs):
        """OpenAI 클라이언트 초기화"""
        api_key = kwargs.get("openai_api_key", os.environ.get("OPENAI_API_KEY"))
        if not api_key:
            raise LLMError("OpenAIClient requires 'openai_api_key'.")
            
        self.client = OpenAI(api_key=api_key)
        self.model_name = kwargs.get("model_name", "gpt-4-turbo")
        self._log(f"OpenAIClient (Default Adapter) initialized for model: {self.model_name}")

    def _prepare_messages(self, prompt: str, chat_history: Optional[List[Dict[str, str]]]) -> List[Dict[str, str]]:
        """[T1 구현] OpenAI의 'messages' 포맷 생성"""
        messages = []
        # (실제로는 chat_history 포맷 변환 로직 필요)
        messages.append({"role": "user", "content": prompt})
        return messages

    def _do_invoke(self, messages: List[Dict[str, str]], **kwargs) -> Any:
        """[T1 구현] OpenAI API 실제 호출"""
        return self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=False,
            **kwargs # (e.g., temperature, max_tokens)
        )

    def _parse_invoke_response(self, raw_response: Any) -> LLMResponse:
        """[T1 구현] OpenAI 응답을 '표준 포맷'으로 변환"""
        text = raw_response.choices[0].message.content
        usage = raw_response.usage
        
        return {
            "text": text,
            "metadata": {
                "model_name": raw_response.model,
                "token_usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                },
                "finish_reason": raw_response.choices[0].finish_reason
            }
        }

    def _do_stream(self, messages: List[Dict[str, str]], **kwargs) -> Iterator[Any]:
        """[T1 구현] OpenAI 스트림 API 호출"""
        return self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=True,
            **kwargs
        )

    def _parse_stream_response(self, raw_stream: Iterator[Any]) -> Iterator[StreamChunk]:
        """[T1 구현] OpenAI 스트림을 '표준 청크'로 변환 (yield)"""
        for chunk in raw_stream:
            delta = chunk.choices[0].delta.content
            
            if delta: # (내용이 있는 청크만)
                yield {
                    "delta": delta,
                    "metadata": {
                        "finish_reason": chunk.choices[0].finish_reason
                    }
                }