from langchain.text_splitter import RecursiveCharacterTextSplitter
from sayou.chunking.splitter.recursive import RecursiveCharacterSplitter
from typing import List

class LangChainRecursiveSplitter(RecursiveCharacterSplitter):
    """
    (Tier 3 - 플러그인) 'LangChain' 라이브러리를 사용해
    '기본' 재귀 분할 로직을 '대체'하는 플러그인.
    """
    component_name = "LangChainRecursiveSplitter"
    # ⭐️ LangChain 전용 타입을 처리
    SUPPORTED_TYPES = ["recursive_char_langchain"] 

    def initialize(self, **kwargs):
        self._log("LangChainRecursiveSplitter (Plugin) is ready.")
        
    def _execute_split_logic(self, text: str, chunk_size: int, chunk_overlap: int, separators: List[str]) -> List[str]:
        """
        [Tier 2 Override] '기본' 로직 대신 LangChain 라이브러리 호출
        """
        self._log(f"Executing LangChain recursive split...")
        
        lc_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators
        )
        
        return lc_splitter.split_text(text)