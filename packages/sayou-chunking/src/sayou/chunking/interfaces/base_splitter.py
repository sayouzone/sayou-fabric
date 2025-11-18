import copy

from abc import abstractmethod
from typing import List, Dict, Any

from sayou.core.base_component import BaseComponent
from ..core.exceptions import ChunkingError

class BaseSplitter(BaseComponent):
    """
    (Tier 1) '콘텐츠 딕셔너리'를 '청크 딕셔너리 리스트'로 분할하는 인터페이스.
    """
    component_name = "BaseSplitter"
    SUPPORTED_TYPES: List[str] = []

    def split(self, split_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        [공통 골격] [수정] T2가 '완전히 포장된' 청크 리스트를 반환.
        """
        split_type = split_request.get("type", "unknown")
        if split_type not in self.SUPPORTED_TYPES:
            raise ChunkingError(f"Handler {self.component_name} does not support type: '{split_type}'")
            
        self._log(f"Handling split request for '{split_type}'...")
        
        try:
            final_chunks = self._do_split(split_request)
            return final_chunks
        
        except Exception as e:
            raise ChunkingError(f"Split failed in {self.component_name}: {e}")

    @abstractmethod
    def _do_split(self, split_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        [T2/T3 구현 필수] [수정] (반환값: 최종 포장된 List[Dict])
        분할, 메타데이터 추출, 공통 메타데이터 결합, 포장까지 모두 수행.
        T1의 _build_chunks 헬퍼를 '반드시' 사용해야 함.
        """
        raise NotImplementedError
    
    def _build_chunks(
        self, 
        text_chunks: List[str], 
        source_metadata: Dict[str, Any],
        parent_id_key: str = "id",
        start_index: int = 0
    ) -> List[Dict[str, Any]]:
        """
        [공통 유틸리티] [수정] T2가 호출하는 '포장 헬퍼' 역할.
        T2가 분할한 텍스트(List[str])에 T2가 제공한 '특수 메타데이터'(source_metadata)를
        결합하여 최종 포장합니다.
        """
        result_chunks = []
        base_metadata = copy.deepcopy(source_metadata)
        parent_id = base_metadata.get(parent_id_key, "doc")
        
        for i, text in enumerate(text_chunks):
            part_index = start_index + i
            chunk_metadata = base_metadata.copy() 
            chunk_metadata.update({
                "chunk_id": f"{parent_id}_chunk_{part_index}",
                "part_index": part_index
            })
            result_chunks.append({
                "chunk_content": text, 
                "metadata": chunk_metadata
            })
        return result_chunks