from typing import List
from ..interfaces.base_splitter import BaseSplitter
from ..utils.schema import Document, Chunk
from ..utils.text_segmenter import TextSegmenter

class RecursiveSplitter(BaseSplitter):
    """
    (Tier 2) 기본 재귀 분할기 (The Standard Infantry).
    - 역할: 주어진 구분자(Separator) 순서대로 텍스트를 안전하게 자릅니다.
    - 특징: Config를 통해 '보호 패턴'을 주입받으면, 그 부분은 절대 자르지 않습니다.
    """
    component_name = "RecursiveSplitter"
    SUPPORTED_TYPES = ["recursive", "default"]

    # 기본 구분자: 문단 -> 줄바꿈 -> 문장 -> 단어 -> 글자
    DEFAULT_SEPARATORS = ["\n\n", "\n", r"(?<=[.?!])\s+", " ", ""]

    def _do_split(self, doc: Document) -> List[Chunk]:
        """
        
        Args:
            doc: 
        
        Returns:
            List: 
        
        Note:
        
        """
        config = doc.metadata.get("config", {})
        doc_id = doc.metadata.get("id", "doc")
        
        # 설정값 로드 (Default 값 방어 로직)
        chunk_size = config.get("chunk_size", 1000)
        chunk_overlap = config.get("chunk_overlap", 100)
        separators = config.get("separators", self.DEFAULT_SEPARATORS)
        protected_patterns = config.get("protected_patterns", [])

        # Tier 1 엔진 실행
        text_chunks = TextSegmenter.split_with_protection(
            text=doc.content,
            separators=separators,
            protected_patterns=protected_patterns,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # 결과 포장
        return [
            Chunk(
                chunk_content=text, 
                metadata={
                    **doc.metadata, # 원본 메타 계승
                    "chunk_id": f"{doc_id}_{i}",
                    "part_index": i
                }
            ) for i, text in enumerate(text_chunks)
        ]