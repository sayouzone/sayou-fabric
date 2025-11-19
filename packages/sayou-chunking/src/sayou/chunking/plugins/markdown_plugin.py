import re
from typing import List, Optional
from ..splitter.recursive import RecursiveSplitter
from ..utils.schema import Document, Chunk
from ..utils.text_segmenter import TextSegmenter

class MarkdownPlugin(RecursiveSplitter):
    """
    (Tier 3) Markdown 전용 플러그인.
    표와 코드블록을 보호하고, Semantic Type을 분류합니다.
    """
    component_name = "MarkdownPlugin"
    SUPPORTED_TYPES = ["markdown", "structure_markdown"]

    # 1. 마크다운용 구분자
    MARKDOWN_SEPARATORS = [r"\n#{1,6} ", "\n\n", "\n", r"(?<=[.?!])\s+", " ", "" ]

    # 2. 보호 패턴 (Regex)
    # Table 정규식을 '한 줄 단위'로 엄격하게 제한하여 re.DOTALL 환경에서도 줄바꿈을 타고 넘어가지 않게 함.
    PROTECTED_PATTERNS = [r"(?s)```.*?```", r"(?m)^(?:\|[^\n]*\|(?:\n|$))+"]

    # 3. 구조적 분할 패턴 (Lookahead Regex)
    # 헤더나 리스트가 새로운 청크의 시작이 되도록 강제함.
    SECTION_SPLIT_PATTERN = r"(?m)^(?=#{1,6} |[-*] |\d+\. )"

    def _do_split(self, doc: Document) -> List[Chunk]:
        config = doc.metadata.get("config", {})
        chunk_size = config.get("chunk_size", 1000)
        doc_id = doc.metadata.get("id", "doc")

        # 헤더 단위로 크게 섹션 분할 (Top-Level Splitting)
        raw_sections = re.split(self.SECTION_SPLIT_PATTERN, doc.content)
        raw_sections = [s for s in raw_sections if s.strip()]

        final_chunks = []
        global_idx = 0
        
        # Context Stack: 현재 유효한 헤더 ID를 추적하기 위한 변수
        # (단순화를 위해 직전 헤더만 추적하지만, 필요시 스택으로 H1>H2>H3 구현 가능)
        current_parent_id: Optional[str] = None
        current_parent_text: Optional[str] = None

        for section in raw_sections:
            header_match = re.match(r"^(#{1,6})\s+(.*)", section.strip().split('\n')[0])
            section_chunks = []
            if header_match:
                header_level = len(header_match.group(1))
                header_text = header_match.group(2).strip()
                header_chunk_id = f"{doc_id}_h_{global_idx}"
                header_chunk = Chunk(
                    chunk_content=f"{header_match.group(1)} {header_text}",
                    metadata={
                        **self._clean_meta(doc.metadata),
                        "chunk_id": header_chunk_id,
                        "part_index": global_idx,
                        "semantic_type": f"h{header_level}",
                        "is_header": True
                    }
                )
                final_chunks.append(header_chunk)
                current_parent_id = header_chunk_id
                current_parent_text = header_text
                global_idx += 1
                
                body_content = section[header_match.end():].strip()
            else:
                body_content = section
            
            if not body_content:
                continue

            # 본문(Body) 미세 분할 (리스트, 텍스트 등)
            # 여기서 Structure-First 전략: 리스트(-) 단위로도 먼저 쪼개고 싶다면 로직 추가 가능
            # 일단은 TextSegmenter로 안전하게 자름
            body_parts = TextSegmenter.split_with_protection(
                body_content, self.MARKDOWN_SEPARATORS, self.PROTECTED_PATTERNS, chunk_size, 0
            )

            for part in body_parts:
                part = part.strip()
                if not part:
                    continue
                
                # 자식 청크 생성 (Parent ID 주입)
                meta = self._clean_meta(doc.metadata)
                meta.update({
                    "chunk_id": f"{doc_id}_part_{global_idx}",
                    "part_index": global_idx,
                    "semantic_type": self._classify_chunk(part),
                    "parent_id": current_parent_id,
                    "section_title": current_parent_text
                })
                final_chunks.append(Chunk(chunk_content=part, metadata=meta))
                global_idx += 1
        return final_chunks

    def _clean_meta(self, meta: dict) -> dict:
        m = meta.copy()
        m.pop("config", None)
        return m

    def _classify_chunk(self, text: str) -> str:
        if text.startswith("|"): return "table"
        if text.startswith("```"): return "code_block"
        if re.match(r"^[-*] ", text): return "list_item"
        return "text"