from abc import abstractmethod
from typing import List, Dict, Any
from sayou.core.base_component import BaseComponent
from sayou.chunking.core.exceptions import ChunkingError

class BaseSplitter(BaseComponent):
    """
    (Tier 1) '문서'를 '청크' 리스트로 분할하는 기본 인터페이스.
    """
    component_name = "BaseSplitter"
    SUPPORTED_TYPES: List[str] = []

    def split(self, split_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        [공통 골격] 청킹(분할) 실행
        
        Args:
            split_request: 

        Returns:
            List: 

        Note:

        """
        split_type = split_request.get("type", "unknown")
        self._log(f"Performing split for type '{split_type}'...")
        try:
            if split_type not in self.SUPPORTED_TYPES:
                raise ChunkingError(f"Unsupported split type: '{split_type}'")
            
            # ⭐️ T2 (Default) 또는 T3 (Override)의 구현 호출
            return self._do_split(split_request)
        except Exception as e:
            raise ChunkingError(f"Split failed: {e}")

    @abstractmethod
    def _do_split(self, split_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        [T2/T3 구현 필수] (결과 포맷: [{"chunk_content": "...", "metadata": {...}}, ...])
        
        Args:
            split_request: 

        Returns:
            List: 

        Note:
        """
        raise NotImplementedError
    
    def _build_chunks(self, text_chunks: List[str], source_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        [공통 유틸리티] 분할된 텍스트 리스트를 표준 청크 Dict 리스트로 포맷팅합니다.
        T2/T3 구현체들이 이 메서드를 재사용할 수 있습니다.
        
        Args:
            text_chunks: 
            source_metadata: 

        Returns:
            List: 

        Note:

        """
        result_chunks = []
        doc_id = source_metadata.get('doc_id', 'doc')
        
        for i, text in enumerate(text_chunks):
            chunk_metadata = source_metadata.copy()
            chunk_metadata.update({
                "chunk_id": f"{doc_id}_part_{i}",
                "part_index": i
            })
            result_chunks.append({
                "chunk_content": text,
                "metadata": chunk_metadata
            })
        return result_chunks