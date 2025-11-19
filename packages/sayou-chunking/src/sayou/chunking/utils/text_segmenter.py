import re
from typing import List

class TextSegmenter:
    """
    Tier 1 유틸리티: 텍스트 분할 엔진.
    'Atomic Block(표, 코드)'을 보호(Protect)하는 기능을 포함합니다.
    """

    @staticmethod
    def split_with_protection(
        text: str, 
        separators: List[str], 
        protected_patterns: List[str],
        chunk_size: int,
        chunk_overlap: int
    ) -> List[str]:
        """
        1. protected_patterns에 해당하는 블록을 찾아 격리합니다.
        2. 격리되지 않은 일반 텍스트만 separators로 재귀 분할합니다.
        3. 순서를 유지하며 합칩니다.
        """
        if not text: return []

        final_chunks = []
        
        # 1. 보호 패턴이 없으면 일반 재귀 분할 수행
        if not protected_patterns:
            return TextSegmenter.recursive_split(text, separators, chunk_size, chunk_overlap)

        # 2. 보호 패턴 통합 (OR 연산)
        combined_pattern = f"({'|'.join(protected_patterns)})"
        
        # 3. 패턴 기준으로 1차 분할 (캡처 그룹 사용 -> 매칭된 것도 결과에 포함됨)
        # re.DOTALL: .이 개행문자도 포함 / re.MULTILINE: ^$가 라인별 매칭
        parts = re.split(combined_pattern, text, flags=re.MULTILINE | re.DOTALL)
        
        for part in parts:
            if not part: continue
            
            is_protected = False
            for pat in protected_patterns:
                if re.fullmatch(pat, part, flags=re.MULTILINE | re.DOTALL):
                    is_protected = True
                    break
            
            if is_protected:
                # 보호된 블록(표)은 절대 쪼개지 않고 통째로 추가
                final_chunks.append(part)
            else:
                # 일반 텍스트는 재귀적으로 잘게 쪼갬
                sub_chunks = TextSegmenter.recursive_split(
                    part, separators, chunk_size, chunk_overlap
                )
                final_chunks.extend(sub_chunks)

        return final_chunks

    @staticmethod
    def recursive_split(text: str, separators: List[str], chunk_size: int, chunk_overlap: int) -> List[str]:
        """(기존 로직) 보호된 블록이 아닌 일반 텍스트를 Top-Down으로 분할"""
        final_chunks = []
        
        if not separators:
            return [text]

        separator = separators[0]
        next_separators = separators[1:]
        
        if separator == "":
            return list(text)

        try:
            splits = re.split(f"({separator})", text)
        except:
            splits = [text]

        current_doc = []
        total_len = 0
        
        for split in splits:
            if not split: continue
            if split == separator:
                if current_doc: current_doc[-1] += split
                continue
            
            if total_len + len(split) > chunk_size:
                if current_doc:
                    final_chunks.append("".join(current_doc))
                    current_doc = []
                    total_len = 0
                
                if len(split) > chunk_size:
                    final_chunks.extend(TextSegmenter.recursive_split(split, next_separators, chunk_size, chunk_overlap))
                else:
                    current_doc.append(split)
                    total_len += len(split)
            else:
                current_doc.append(split)
                total_len += len(split)
        
        if current_doc:
            final_chunks.append("".join(current_doc))
            
        return final_chunks