import re
from typing import List

from ..splitter.recursive import RecursiveSplitter
from ..utils.schema import Document, Chunk
from ..utils.text_segmenter import TextSegmenter

class StructureSplitter(RecursiveSplitter):
    """
    (Tier 2) 범용 구조 분할기 (The Generic Architect).
    - 역할: 사용자가 정의한 '구조 패턴(Regex)'을 기준으로 문서를 크게 나눕니다.
    - 특징: MarkdownPlugin처럼 전용 로직이 없어도, 패턴만 넣으면 구조화된 청킹이 가능합니다.
    """
    component_name = "StructureSplitter"
    SUPPORTED_TYPES = ["structure"]

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
        chunk_size = config.get("chunk_size", 1000)

        # 1. 사용자 정의 구조 패턴 가져오기
        # 예: 법률 문서라면 r"제\d+조" 같은 패턴이 들어옴
        structure_pattern = config.get("structure_pattern", r"\n\n") 

        # 2. 구조적 분할 (Lookahead를 적용하여 패턴 앞에서 자름)
        # 패턴이 단순히 구분자가 아니라 '헤더' 역할을 하도록 (?=...) 처리 시도
        try:
            # 사용자가 괄호를 안 넣었을 수 있으니 안전하게 그룹핑
            split_regex = f"(?m)(?={structure_pattern})" 
            sections = re.split(split_regex, doc.content)
        except Exception:
            # 정규식 오류 시 기본 분할
            sections = doc.content.split("\n\n")

        final_chunks = []
        global_idx = 0

        for section in sections:
            section = section.strip()
            if not section: continue

            # 3. 섹션 내부 미세 분할 (Recursive 상속 기능 활용)
            # 섹션이 chunk_size보다 크면 Recursive하게 자름
            if len(section) > chunk_size:
                # 부모(Recursive)의 로직을 빌려 쓰되, Document를 새로 포장해서 넘김
                # (주의: 여기서 super()._do_split을 바로 부르면 메타데이터가 꼬일 수 있어 직접 Segmenter 호출)
                sub_parts = TextSegmenter.split_with_protection(
                    section,
                    config.get("separators", self.DEFAULT_SEPARATORS),
                    config.get("protected_patterns", []),
                    chunk_size,
                    config.get("chunk_overlap", 50)
                )
                for part in sub_parts:
                    final_chunks.append(self._pack_chunk(part, doc.metadata, doc_id, global_idx, is_structure=False))
                    global_idx += 1
            else:
                # 섹션이 작으면 통째로 청크화 (구조 보존)
                final_chunks.append(self._pack_chunk(section, doc.metadata, doc_id, global_idx, is_structure=True))
                global_idx += 1

        return final_chunks

    def _pack_chunk(self, text, meta, doc_id, idx, is_structure):
        """
        
        Args:
            doc: 
        
        Returns:
            List: 
        
        Note:

        """
        m = meta.copy()
        m.pop("config", None)
        m.update({
            "chunk_id": f"{doc_id}_{idx}",
            "part_index": idx,
            "semantic_type": "structure_section" if is_structure else "text_fragment"
        })
        return Chunk(text, m)