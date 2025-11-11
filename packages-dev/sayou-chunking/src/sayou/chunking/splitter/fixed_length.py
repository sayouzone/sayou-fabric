from sayou.chunking.interfaces.base_splitter import BaseSplitter, ChunkingError
from typing import List, Dict, Any

class FixedLengthSplitter(BaseSplitter):
    """
    (Tier 2 - 기본 기능) 고정된 길이로 텍스트를 분할합니다.
    """
    component_name = "FixedLengthSplitter"
    SUPPORTED_TYPES = ["fixed_length"]

    def _do_split(self, split_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        content = split_request.get("content")
        if not content: raise ChunkingError("Missing 'content' field.")
            
        chunk_size = split_request.get("chunk_size", 1000)
        chunk_overlap = split_request.get("chunk_overlap", 0)
        source_metadata = split_request.get("metadata", {})
        
        text_chunks = [
            content[i:i + chunk_size] 
            for i in range(0, len(content), chunk_size - chunk_overlap)
        ]
        
        return self._build_chunks(text_chunks, source_metadata)