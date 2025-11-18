import re
from sayou.chunking.interfaces.base_splitter import BaseSplitter, ChunkingError
from typing import List, Dict, Any

class StructureBasedSplitter(BaseSplitter):
    """
    (Tier 2 - 기본 기능) 특정 '구조' (e.g., Markdown 헤더)를
    기준으로 텍스트를 분할합니다.
    """
    component_name = "StructureBasedSplitter"
    SUPPORTED_TYPES = ["structure_markdown"] # e.g., Markdown

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
        
        # 기본 구분자: Markdown H1, H2
        separators = split_request.get("separators", ["\n# ", "\n## "])
        source_metadata = split_request.get("metadata", {})
        
        # (실제 로직)
        # 1. 구분자 기준으로 텍스트 분할 (e.g., re.split)
        # 2. 분할된 텍스트가 너무 클 경우, 'recursive_char' (T2)를
        #    '내부적으로' 호출하여 2차 분할할 수 있습니다 (Composition).
        # 3. 혹은 단순하게 구현합니다.
        
        # (단순 예시: H1(#) 기준으로만 분할)
        text_chunks = re.split(r'(\n# [^\n]+)', content)
        
        # (... 분할된 청크 재조합 및 후처리 로직 ...)
        # ...

        # (임시 반환 - 실제 구현 필요)
        self._log("Structure splitting (Markdown) is not fully implemented yet.")
        text_chunks = [content[:1000]] # 임시
        
        return self._build_chunks(text_chunks, source_metadata)