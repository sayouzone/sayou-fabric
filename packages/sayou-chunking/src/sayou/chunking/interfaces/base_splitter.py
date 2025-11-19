from abc import abstractmethod
from typing import List, Dict, Any
from sayou.core.base_component import BaseComponent
from ..core.exceptions import ChunkingError
from ..utils.schema import Document, Chunk

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
        
        try:
            if split_type not in self.SUPPORTED_TYPES:
                raise ChunkingError(f"Handler {self.component_name} does not support type: '{split_type}'")
            
            if "content" not in split_request:
                raise ChunkingError("Request requires 'content' field.")

            # Dict -> Document 변환
            doc = Document(
                content=split_request.get("content", ""),
                metadata=split_request.get("metadata", {})
            )

            # Config 정보도 메타데이터에 병합 (Prioritize request-level config)
            doc.metadata["config"] = {
                "chunk_size": split_request.get("chunk_size", 1000),
                "chunk_overlap": split_request.get("chunk_overlap", 100),
                **doc.metadata.get("config", {})
            }

            # 딕셔너리(split_request)가 아니라 객체(doc)를 넘겨야 함!
            chunks = self._do_split(doc)
            
            # Chunk(Obj) -> Dict 변환 (Pipeline 호환성)
            return self._build_chunks(chunks)
            
        except Exception as e:
            raise ChunkingError(f"Split failed in {self.component_name}: {e}")

    @abstractmethod
    def _do_split(self, doc: Document) -> List[Chunk]:
        """
        [T2/T3 구현] 반드시 List[Chunk] 객체를 반환해야 함.
        
        Args:
            split_request: 

        Returns:
            List: 

        Note:
        """
        raise NotImplementedError
    
    def _build_chunks(self, chunks: List[Any]) -> List[Dict[str, Any]]:
        """
        Chunk 객체 리스트를 Dict 리스트로 변환하는 헬퍼
        
        Args:
            text_chunks: 
            source_metadata: 

        Returns:
            List: 

        Note:

        """
        result_chunks = []
        # chunks가 이미 List[Chunk]라고 가정하고 변환
        for chunk in chunks:
            if isinstance(chunk, Chunk):
                result_chunks.append({
                    "chunk_content": chunk.chunk_content,
                    "metadata": chunk.metadata
                })
            # 만약 실수로 str 리스트가 오면 방어 로직 (T2 개발 편의)
            elif isinstance(chunk, str):
                result_chunks.append({
                    "chunk_content": chunk,
                    "metadata": {}
                })
        return result_chunks