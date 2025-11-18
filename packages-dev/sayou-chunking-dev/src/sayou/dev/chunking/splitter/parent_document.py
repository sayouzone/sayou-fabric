from sayou.chunking.interfaces.base_splitter import BaseSplitter, ChunkingError
from typing import List, Dict, Any

class ParentDocumentSplitter(BaseSplitter):
    """
    (Tier 2 - 기본 기능) '작은 자식 청크'와 '큰 부모 청크'를
    모두 생성하는 전략을 지원합니다.
    """
    component_name = "ParentDocumentSplitter"
    SUPPORTED_TYPES = ["parent_child"]

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
        
        # (이 전략은 T2 <-> T2 Composition을 사용하기 좋습니다)
        # e.g., parent_splitter_type = "recursive_char"
        # e.g., child_splitter_type = "fixed_length"
        
        parent_chunk_size = split_request.get("parent_chunk_size", 2000)
        child_chunk_size = split_request.get("child_chunk_size", 400)
        source_metadata = split_request.get("metadata", {})

        # (실제 로직)
        # 1. '부모 청크'를 생성합니다 (e.g., RecursiveCharacterSplitter 사용).
        # 2. 각 '부모 청크' 내에서 '자식 청크'를 생성합니다.
        # 3. '자식 청크'의 metadata에 'parent_chunk_id'를 추가합니다.
        
        # (이 전략은 반환 값이 다를 수 있습니다. e.g., 부모/자식 리스트)
        # (여기서는 '자식 청크'만 반환한다고 가정)
        
        self._log("ParentDocument splitting is not fully implemented yet.")
        
        # (임시) 자식 청크 1개만 생성
        child_chunk_text = content[:child_chunk_size]
        child_metadata = source_metadata.copy()
        child_metadata["parent_doc_id"] = source_metadata.get("doc_id", "doc")
        
        # (T1의 _build_chunks 사용 불가. 메타데이터가 다름)
        result_chunks = [{
            "chunk_content": child_chunk_text,
            "metadata": child_metadata,
            "chunk_id": f"{source_metadata.get('doc_id', 'doc')}_child_0"
        }]
        
        return result_chunks