from abc import abstractmethod
from typing import Dict, Any, Iterator, List, Optional
from sayou.core.base_component import BaseComponent
from sayou.llm.core.exceptions import LLMError
# from sayou.llm.core.standard_types import LLMResponse, StreamChunk # (표준 응답 DTO)

# (간결성을 위해 DTO 대신 Dict 사용)
LLMResponse = Dict[str, Any]
StreamChunk = Dict[str, Any]

class BaseLLMClient(BaseComponent):
    """
    (Tier 1) 모든 LLM 서비스 제공자(OpenAI, Anthropic 등)를
    추상화하는 표준 클라이언트 인터페이스.
    
    모든 클라이언트는 'invoke'와 'stream' 메서드를 구현해야 하며,
    '벤더 중립적인' 표준 응답(Dict)을 반환해야 합니다.
    """
    component_name = "BaseLLMClient"
    SUPPORTED_TYPES: List[str] = [] # e.g., "openai_chat", "anthropic_chat"

    def invoke(self, 
        prompt: str, 
        chat_history: Optional[List[Dict[str, str]]] = None,
        **kwargs) -> LLMResponse:
        """
        [공통 골격] LLM을 1회 호출하고 '표준 응답'을 반환합니다. (Non-Streaming)
        """
        self._log(f"Invoking LLM for prompt: '{prompt[:40]}...'")
        try:
            # 1. 벤더별 메시지 포맷으로 변환 (T2/T3가 구현)
            vendor_messages = self._prepare_messages(prompt, chat_history)
            
            # 2. 벤더 API 실제 호출 (T2/T3가 구현)
            raw_response = self._do_invoke(vendor_messages, **kwargs)
            
            # 3. 벤더 응답을 '표준 포맷'으로 변환 (T2/T3가 구현)
            standard_response = self._parse_invoke_response(raw_response)
            
            self._log(f"Invocation successful. (Usage: {standard_response.get('metadata', {}).get('token_usage')})")
            return standard_response
            
        except Exception as e:
            raise LLMError(f"LLM invocation failed: {e}")

    def stream(self, 
        prompt: str, 
        chat_history: Optional[List[Dict[str, str]]] = None,
        **kwargs) -> Iterator[StreamChunk]:
        """
        [공통 골격] LLM을 스트리밍 호출하고 '표준 청크' 이터레이터를 반환합니다.
        """
        self._log(f"Streaming LLM for prompt: '{prompt[:40]}...'")
        try:
            vendor_messages = self._prepare_messages(prompt, chat_history)
            raw_stream = self._do_stream(vendor_messages, **kwargs)
            
            # ⭐️ 스트림 파싱 로직을 제너레이터로 래핑
            yield from self._parse_stream_response(raw_stream)
            
        except Exception as e:
            raise LLMError(f"LLM streaming failed: {e}")

    # --- [ T2/T3 구현 필수 ] ---

    @abstractmethod
    def _prepare_messages(self, prompt: str, chat_history: Optional[List[Dict[str, str]]]) -> Any:
        """[T2 구현] (e.g., OpenAI의 [{"role": "user", "content": ...}] 포맷 생성)"""
        raise NotImplementedError

    @abstractmethod
    def _do_invoke(self, messages: Any, **kwargs) -> Any:
        """[T2 구현] (e.g., client.chat.completions.create(...) 호출)"""
        raise NotImplementedError

    @abstractmethod
    def _parse_invoke_response(self, raw_response: Any) -> LLMResponse:
        """
        [T2 구현] (e.g., OpenAI 응답 객체를 표준 Dict로 변환)
        (표준 포맷: {"text": "...", "metadata": {"token_usage": {...}, "model_name": "..."}})
        """
        raise NotImplementedError
    
    @abstractmethod
    def _do_stream(self, messages: Any, **kwargs) -> Iterator[Any]:
        """[T2 구현] (e.g., client.chat.completions.create(stream=True) 호출)"""
        raise NotImplementedError

    @abstractmethod
    def _parse_stream_response(self, raw_stream: Iterator[Any]) -> Iterator[StreamChunk]:
        """
        [T2 구현] (e.g., OpenAI 스트림 청크를 표준 Dict로 변환)
        (표준 포맷: {"delta": "...", "metadata": {"finish_reason": "..."}})
        """
        raise NotImplementedError