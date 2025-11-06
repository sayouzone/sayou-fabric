# (필요) pip install torch transformers accelerate
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, Pipeline, pipeline
from sayou.llm.interfaces.base_llm_client import BaseLLMClient, LLMResponse, StreamChunk
from sayou.llm.core.exceptions import LLMError
from typing import Dict, Any, Iterator, List, Optional

class TransformersClient(BaseLLMClient):
    """
    (Tier 2 - 공식 어댑터)
    'HuggingFace Transformers' (safetensors) 모델을
    메모리에 직접 로드하여 'BaseLLMClient'(T1)로 래핑합니다.
    """
    component_name = "TransformersClient"
    SUPPORTED_TYPES = ["transformers_native"] # 👈 이 클라이언트의 고유 타입

    def initialize(self, **kwargs):
        """
        'model_name' (HuggingFace ID)을 받아 모델과 토크나이저를 로드합니다.
        """
        self.model_name = kwargs.get("model_name") # (e.g., "gemma-1.1-2b-it")
        if not self.model_name:
            raise LLMError("TransformersClient requires 'model_name'.")
            
        device = kwargs.get("device", "cuda" if torch.cuda.is_available() else "cpu")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                device_map=device,
                torch_dtype=torch.bfloat16 # (성능을 위한 설정 예시)
            )
            
            # (HuggingFace Pipeline을 사용하면 더 편리하게 래핑 가능)
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device_map=device
            )
        except Exception as e:
            raise LLMError(f"Failed to load Transformers model {self.model_name}: {e}")
            
        self._log(f"TransformersClient (T2 Adapter) initialized. Model: {self.model_name} on {device}")

    def _prepare_messages(self, prompt: str, chat_history: Optional[List[Dict[str, str]]]) -> Any:
        """[T1 구현] Transformers Pipeline이 사용할 'messages' 포맷 생성"""
        # (채팅 히스토리와 쿼리를 템플릿에 맞게 조합)
        messages = []
        # for msg in chat_history:
        #     messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": prompt})
        
        # ⭐️ Pipeline.tokenizer.apply_chat_template을 사용
        return self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    def _do_invoke(self, messages_prompt: str, **kwargs) -> Any:
        """[T1 구현] Transformers Pipeline (model.generate) 실제 호출"""
        
        # ⭐️ HuggingFace Pipeline 호출
        return self.pipeline(
            messages_prompt,
            max_new_tokens=kwargs.get("max_tokens", 512),
            do_sample=True,
            temperature=kwargs.get("temperature", 0.7),
            # (Pipeline은 'usage' 정보를 기본으로 반환하지 않음)
        )

    def _parse_invoke_response(self, raw_response: List[Dict[str, Any]]) -> LLMResponse:
        """[T1 구현] Pipeline 응답을 '표준 포맷'으로 변환"""
        # (raw_response[0]['generated_text'])
        # (파이프라인이 프롬프트까지 반환하므로, 답변 부분만 추출하는 로직 필요)
        full_text = raw_response[0]['generated_text']
        
        # (이 부분은 모델 템플릿에 따라 복잡해질 수 있음 - 프롬프트 제거)
        answer_text = full_text # (임시로 전체 텍스트 반환)
        
        return {
            "text": answer_text.strip(),
            "metadata": {
                "model_name": self.model_name,
                "token_usage": None, # ⭐️ Transformers는 토큰 수 추적이 어려움
                "finish_reason": "stop"
            }
        }
    
    # (스트리밍 구현은 TextIteratorStreamer 등을 사용하여 별도 구현 필요)
    @abstractmethod
    def _do_stream(self, messages: Any, **kwargs) -> Iterator[Any]:
        raise NotImplementedError("TransformersClient streaming not implemented yet.")

    @abstractmethod
    def _parse_stream_response(self, raw_stream: Iterator[Any]) -> Iterator[StreamChunk]:
        raise NotImplementedError