import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import Dict, Any, Iterator, List, Optional

# 1. T1 인터페이스 임포트
from sayou.llm.interfaces.base_llm_client import BaseLLMClient, LLMResponse, StreamChunk
from sayou.llm.core.exceptions import LLMError
# (sayou.core.base_component는 BaseLLMClient가 이미 상속받았다고 가정)

class HuggingFaceNativeClient(BaseLLMClient):
    """
    (Tier 3 - 커스텀 플러그인)
    로컬에 저장된 HuggingFace 원본(safetensors) 모델을
    'AutoModelForCausalLM.generate()'로 직접 호출합니다.
    
    이 방식은 모델의 '채팅 템플릿'을 T1에서 완벽하게 제어할 수 있게 합니다.
    """
    component_name = "HuggingFaceNativeClient"
    SUPPORTED_TYPES = ["hf_native"] # 👈 이 커스텀 플러그인의 타입

    def initialize(self, **kwargs):
        """
        'model_path' (로컬 경로)를 받아 모델과 토크나이저를 로드합니다.
        
        Args:
            model_path (str): (e.g., "C:/models/gemma-3-1b-it")
            device (str, optional): (e.g., "cuda", "cpu")
            torch_dtype (Any, optional): (e.g., torch.bfloat16)
        """
        self.model_path = kwargs.get("model_path")
        if not self.model_path:
            raise LLMError("HuggingFaceNativeClient requires 'model_path'.")
            
        self.device = kwargs.get("device", "cuda" if torch.cuda.is_available() else "cpu")
        self.torch_dtype = kwargs.get("torch_dtype", torch.bfloat16 if self.device == "cuda" else torch.float32)
        
        try:
            self._log(f"Loading Tokenizer from: {self.model_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            
            self._log(f"Loading Model to {self.device} from: {self.model_path}...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                device_map=self.device,
                torch_dtype=self.torch_dtype
            )
            self._log("Model loading complete.")
            
        except Exception as e:
            raise LLMError(f"Failed to load Transformers model {self.model_path}: {e}")

    # --- [ T1 인터페이스 구현 ] ---

    def _prepare_messages(self, prompt: str, chat_history: Optional[List[Dict[str, str]]]) -> Any:
        """[T1 구현] 모델 고유의 '채팅 템플릿'을 적용하고 토큰화합니다."""
        
        messages = chat_history or []
        messages.append({"role": "user", "content": prompt})
        
        # ⭐️ 토크나이저가 알고 있는 고유 템플릿(Gemma, Llama 등)을 적용
        try:
            input_ids = self.tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True, # 👈 'model\n' 프롬프트 추가
                tokenize=True,
                return_tensors="pt" # 👈 PyTorch 텐서로 반환
            ).to(self.device)
            return input_ids
        except Exception as e:
            self._log(f"Warning: apply_chat_template failed. Using simple prompt. {e}")
            # (채팅 템플릿이 없는 모델을 위한 폴백)
            return self.tokenizer(prompt, return_tensors="pt").input_ids.to(self.device)

    def _do_invoke(self, input_ids: torch.Tensor, **kwargs) -> Any:
        """[T1 구현] 'model.generate()'를 직접 호출합니다."""
        
        # ⭐️ (T3 로직) 입력 토큰 길이를 저장 (응답 파싱에 사용)
        self._last_input_length = input_ids.shape[1]
        
        # (모델 생성 옵션)
        generation_kwargs = {
            "max_new_tokens": kwargs.get("max_tokens", 512),
            "temperature": kwargs.get("temperature", 0.7),
            "eos_token_id": self.tokenizer.eos_token_id,
        }
        
        # ⭐️ 원본 모델 생성
        outputs = self.model.generate(input_ids, **generation_kwargs)
        return outputs

    def _parse_invoke_response(self, raw_response_tensor: torch.Tensor) -> LLMResponse:
        """[T1 구현] 원본 텐서 응답을 '표준 포맷'으로 변환"""
        
        # ⭐️ 핵심: 입력 텐서 길이를 제외한 '새로 생성된' 토큰만 디코딩
        output_ids = raw_response_tensor[0][self._last_input_length:]
        
        text = self.tokenizer.decode(output_ids, skip_special_tokens=True)
        
        return {
            "text": text.strip(),
            "metadata": {
                "model_name": self.model_path,
                "token_usage": None, # (generate()는 토큰 수 반환 안 함)
                "finish_reason": "stop"
            }
        }

    # (스트리밍은 TextIteratorStreamer를 사용하여 별도 구현 필요)
    def _do_stream(self, messages: Any, **kwargs) -> Iterator[Any]:
        self._log("Streaming not implemented for HFNativeClient yet.")
        raise NotImplementedError("HFNativeClient streaming not implemented yet.")

    def _parse_stream_response(self, raw_stream: Iterator[Any]) -> Iterator[StreamChunk]:
        raise NotImplementedError