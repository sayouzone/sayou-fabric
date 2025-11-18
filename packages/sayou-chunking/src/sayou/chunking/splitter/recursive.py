import re

from typing import List, Dict, Any

from ..interfaces.base_splitter import BaseSplitter, ChunkingError

class RecursiveCharacterSplitter(BaseSplitter):
    """
    (Tier 2) 기본 제공하는 순수 Python 기반 재귀 분할기.
    '큰 조각을 재귀적으로 분할'하고, '작은 조각을 병합'합니다.
    '테이블'과 '코드' 블록을 보호합니다.
    """
    component_name = "RecursiveCharacterSplitter"
    SUPPORTED_TYPES = ["recursive_char"]

    def _do_split(self, split_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        content = split_request.get("content")
        if not isinstance(content, str):
            raise ChunkingError("Request requires a 'content' field (str).")
            
        chunk_size = split_request.get("chunk_size", 1000)
        chunk_overlap = split_request.get("chunk_overlap", 100)
        separators = ["\n\n", "(?<=[\.?!])\s+", "\s+"]
        source_metadata = split_request.get("metadata", {})
        splits = self._split_text_recursive(content, separators)
        merged_splits = self._merge_splits(splits, chunk_size, chunk_overlap)
        
        return self._build_chunks(merged_splits, source_metadata)

    def _split_text_recursive(self, text: str, separators: List[str]) -> List[str]:
        """재귀적으로 텍스트를 분할 (테이블 등 Atomic 블록 보호)"""
        final_splits: List[str] = []
        if not text:
            return []

        table_regex = r"(?m)^(?:\|.*\|[\n]?)+"
        code_regex = r"(?s)```.*?```" 
        atomic_regex = f"({code_regex}|{table_regex})"
        
        try:
            parts = re.split(atomic_regex, text)
        except:
            parts = [text]

        for i, part in enumerate(parts):
            if not part: continue
                
            if i % 2 == 1: 
                final_splits.append(part)
                continue

            if not separators:
                if part: final_splits.append(part)
                continue

            primary_separator = separators[0]
            remaining_separators = separators[1:]

            try:
                tokens = re.split(f"({primary_separator})", part)
            except:
                tokens = [part]

            for tok in tokens:
                if tok == "":
                    continue

                if re.fullmatch(primary_separator, tok):
                    final_splits.append(tok)
                    continue

                final_splits.extend(
                    self._split_text_recursive(tok, remaining_separators)
                )
                    
        return final_splits

    def _merge_splits(self, splits: List[str], chunk_size: int, chunk_overlap: int) -> List[str]:
        """분할된 '작은' 조각들을 chunk_size에 맞게 '병합'합니다."""
        final_chunks: List[str] = []
        current_buffer: List[str] = [] 
        current_length = 0
        
        for split in splits:
            if not split:
                continue
                
            split_len = len(split)

            if split_len > chunk_size and (split.strip().startswith("|") or split.strip().startswith("```")):
                self._log(f"Warning: Atomic block (table/code) is larger than chunk_size ({split_len}). Adding as single chunk.")
                if current_buffer:
                    final_chunks.append("".join(current_buffer))
                final_chunks.append(split)
                current_buffer = []
                current_length = 0
                continue

            if current_length + split_len > chunk_size and current_buffer:
                final_chunks.append("".join(current_buffer))
                current_buffer = [split]
                current_length = split_len
            
            else:
                if current_buffer and not split.isspace() and not current_buffer[-1].isspace():
                    current_buffer.append(" ")

                current_buffer.append(split)
                current_length += split_len

        if current_buffer:
            final_chunks.append("".join(current_buffer))

        return [chunk.strip() for chunk in final_chunks if chunk.strip()]