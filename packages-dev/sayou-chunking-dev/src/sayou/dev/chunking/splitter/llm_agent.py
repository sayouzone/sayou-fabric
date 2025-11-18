from sayou.chunking.interfaces.base_splitter import BaseSplitter, ChunkingError
from typing import List, Dict, Any

class AgenticSplitter(BaseSplitter):
    """
    (Tier 2 - 기본 기능) LLM/Agent를 사용하여
    문맥적으로 가장 의미 있는 지점을 찾아 분할합니다. (초고급)
    """
    component_name = "AgenticSplitter"
    SUPPORTED_TYPES = ["llm_agent"]

    def initialize(self, **kwargs):
        """
        LLM 클라이언트(e.g., OpenAI)를 주입받아야 합니다.

        Args:
            **kwargs): 
        """
        # self._llm_client: BaseLLMClient = kwargs.get("llm_client")
        # if not self._llm_client:
        #     raise ChunkingError("AgenticSplitter requires 'llm_client'.")
            
        self._prompt_template = kwargs.get(
            "prompt_template", 
            "다음 텍스트를 의미적으로 가장 중요한 단락 단위로 분할하고 JSON 리스트로 반환해: {content}"
        )
        self._log("AgenticSplitter (Default) initialized.")

    def _do_split(self, split_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        
        
        Args:
            split_request: 

        Returns:
            List: 

        Note:

        """
        content = split_request.get("content")
        if not content: raise ChunkingError("Missing 'content' field.")
        source_metadata = split_request.get("metadata", {})

        # (실제 로직)
        # 1. 프롬프트 생성
        # prompt = self._prompt_template.format(content=content)
        
        # 2. LLM 호출
        # response = self._llm_client.invoke(prompt)
        
        # 3. LLM의 응답 (JSON/Text)을 파싱하여 text_chunks 생성
        
        self._log("Agentic splitting is not implemented (requires LLM client).")
        text_chunks = [content[:1000]] # 임시
        
        return self._build_chunks(text_chunks, source_metadata)