import re

from typing import List, Dict, Any

from ..interfaces.base_splitter import BaseSplitter, ChunkingError
from ..splitter.recursive import RecursiveCharacterSplitter

class StructureBasedSplitter(BaseSplitter):
    """
    (Tier 2) '구조'를 기준으로 1차 분할하고, '시맨틱 메타데이터'를 각 청크에 포장합니다.
    """
    component_name = "StructureBasedSplitter"
    SUPPORTED_TYPES = ["structure_markdown"]

    def initialize(self, **kwargs):
        self.fallback_splitter = RecursiveCharacterSplitter()
        self.fallback_splitter.initialize(**kwargs)
        self._log("Initialized with RecursiveCharacterSplitter as fallback.")

    def _do_split(self, split_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        content = split_request.get("content")
        if not isinstance(content, str):
            raise ChunkingError("Request requires a 'content' field (str).")
        
        chunk_size = split_request.get("chunk_size", 1000)
        chunk_overlap = split_request.get("chunk_overlap", 100)
        source_metadata = split_request.get("metadata", {})
        pattern = r"(?=^\s*(# |## |### |- |\* |\d+\. ))"

        # 1. 1차 분할 (시맨틱)
        try:
            semantic_splits = re.split(pattern, content, flags=re.MULTILINE)
            if semantic_splits and not semantic_splits[0].strip():
                semantic_splits = semantic_splits[1:]
        except Exception as e:
            self._log(f"Regex split failed: {e}. Splitting as one chunk.")
            semantic_splits = [content]

        # 2. 2차 분할 및 '포장'
        final_chunks: List[Dict[str, Any]] = []
        global_part_index = 0
        
        for chunk_text in semantic_splits:
            if not chunk_text or not chunk_text.strip():
                continue
            
            chunk_semantic_meta = self._extract_semantic_metadata(chunk_text)
            current_chunk_metadata = {**source_metadata, **chunk_semantic_meta}
            
            if len(chunk_text) <= chunk_size:
                # 2a. 조각이 충분히 작으면: '단서'와 함께 T1 헬퍼로 '포장'
                packaged_chunks = self._build_chunks(
                    [chunk_text], 
                    current_chunk_metadata,
                    start_index=global_part_index
                )
                final_chunks.extend(packaged_chunks)
                global_part_index += len(packaged_chunks)
            else:
                # 2b. 조각이 너무 크면: T2 '부품'(Recursive)에 위임
                self._log(f"Chunk starting with '{chunk_text[:30]}...' is too large ({len(chunk_text)}). Using fallback splitter.")
                
                fallback_request = {
                    "content": chunk_text,
                    "type": "recursive_char",
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                    "separators": [
                        r"\n\n",                     # paragraph
                        r"(?<=[.!?])\s+",            # sentence boundary
                        r"\n",                       # single newline fallback
                        r""                          # character-level fallback
                    ],
                    "metadata": current_chunk_metadata
                }
                
                smaller_chunks = self.fallback_splitter.split(fallback_request)
                for chunk in smaller_chunks:
                    chunk_text = chunk["chunk_content"]
                    merged_meta = {**current_chunk_metadata, **chunk["metadata"]}
                    
                    new_chunk_id = f'{merged_meta["id"]}_chunk_{global_part_index}'
                    merged_meta["chunk_id"] = new_chunk_id
                    merged_meta["part_index"] = global_part_index
                    final_chunks.append({
                        "chunk_content": chunk_text,
                        "metadata": merged_meta
                    })
                    global_part_index += 1
                
        return final_chunks

    def _extract_semantic_metadata(self, chunk_text: str) -> Dict[str, Any]:
        """청크의 시작 부분을 분석해 시맨틱 메타데이터 추출"""
        meta = {"semantic_type": "text"}
        
        if re.match(r"^\s*# ", chunk_text):
            meta["semantic_type"] = "h1"
        elif re.match(r"^\s*## ", chunk_text):
            meta["semantic_type"] = "h2"
        elif re.match(r"^\s*### ", chunk_text):
            meta["semantic_type"] = "h3"
        elif re.match(r"^\s*[-*] ", chunk_text):
            meta["semantic_type"] = "list_item_unordered"
        elif re.match(r"^\s*\d+\. ", chunk_text):
            meta["semantic_type"] = "list_item_ordered"
        elif re.match(r"^\s*\|", chunk_text):
            meta["semantic_type"] = "table" 
        
        return meta