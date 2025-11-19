from sayou.chunking.interfaces.base_splitter import BaseSplitter, ChunkingError
from typing import List, Dict, Any

class RecursiveCharacterSplitter(BaseSplitter):
    """
    (Tier 2 - 기본 기능) 'sayou'가 기본 제공하는
    순수 Python 기반의 재귀적 문자 분할 전략.
    """
    component_name = "RecursiveCharacterSplitter"
    SUPPORTED_TYPES = ["recursive_char"] # 👈 기본 타입

    def initialize(self, **kwargs):
        self._log("RecursiveCharacterSplitter (Default) is ready.")

    def _do_split(self, split_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """[Tier 1 구현] 파라미터 검증 및 '기본' 분할 로직 실행"""
        """
        
        
        Args:
            text_chunks: 
            source_metadata: 

        Returns:
            List: 

        Note:

        """
        
        content = split_request.get("content")
        if not content or not isinstance(content, str):
            raise ChunkingError("Request requires a 'content' field (str).")
            
        chunk_size = split_request.get("chunk_size", 1000)
        chunk_overlap = split_request.get("chunk_overlap", 100)
        separators = split_request.get("separators", ["\n\n", "\n", " ", ""])
        source_metadata = split_request.get("metadata", {})

        # ⭐️ '기본' 분할 로직 실행 (재정의 가능하도록 분리)
        text_chunks = self._execute_split_logic(
            content, chunk_size, chunk_overlap, separators
        )

        # [T1 유틸리티 사용] 표준 포맷으로 래핑
        return self._build_chunks(text_chunks, source_metadata)

    def _execute_split_logic(self, text: str, chunk_size: int, chunk_overlap: int, separators: List[str]) -> List[str]:
        """
        [T3가 Override 가능] '기본' 재귀 분할 로직.
        (LangChain의 로직을 단순화하여 모방)        
        
        Args:
            text: 
            chunk_size: 
            chunk_overlap: 
            separators: 

        Returns:
            List: 

        Note:

        """
        self._log(f"Executing default recursive split...")
        
        final_chunks = []
        if not separators:
            # (... 고정 길이 분할 로직 ...)
            return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - chunk_overlap)]

        primary_separator = separators[0]
        remaining_separators = separators[1:]
        
        splits = text.split(primary_separator)
        
        good_splits = []
        for s in splits:
            if len(s) < chunk_size:
                good_splits.append(s)
            else:
                # ⭐️ 재귀 호출
                good_splits.extend(
                    self._execute_split_logic( # 👈 self. 재귀
                        s, chunk_size, chunk_overlap, remaining_separators
                    )
                )
        
        # (실제로는 여기서 Overlap을 고려한 Merge 로직이 필요함)
        # (지금은 단순화를 위해 필터링만 적용)
        final_chunks = [s for s in good_splits if s.strip()]
        return final_chunks