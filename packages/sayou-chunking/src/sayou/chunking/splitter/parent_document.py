from typing import List

from ..interfaces.base_splitter import BaseSplitter
from ..utils.schema import Document, Chunk
from ..splitter.recursive import RecursiveSplitter
from ..splitter.structure import StructureSplitter

class ParentDocumentSplitter(BaseSplitter):
    """
    Parent-Child 전략 복합체 (The Commander).
    - 역할: '부모 전략'으로 문맥(Context)을 잡고, '자식 전략'으로 검색(Retrieval) 단위를 만듭니다.
    - 특징: 단순 Fixed-Fixed 뿐만 아니라, Structure-Recursive, Semantic-Recursive 등 조합이 가능합니다.
    """
    component_name = "ParentDocumentSplitter"
    SUPPORTED_TYPES = ["parent_document"]

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
        
        # 1. 전략 선택 (Strategy Selection)
        strategy_type = config.get("parent_strategy", "recursive") # default: size-based
        
        if strategy_type == "structure":
            # 구조(Regex) 기반 부모 분할
            parent_splitter = StructureSplitter()
        else:
            # 크기(Size) 기반 부모 분할 (Default)
            parent_splitter = RecursiveSplitter()
            
        # 자식은 보통 Recursive(미세 분할)를 사용
        child_splitter = RecursiveSplitter()

        final_chunks = []

        # 2. [Phase 1] 부모 청크 생성 (The Context)
        # 부모용 설정 주입 (예: 2000자)
        parent_config = config.copy()
        parent_config["chunk_size"] = config.get("parent_chunk_size", 2000)
        
        parent_doc_input = Document(content=doc.content, metadata={**doc.metadata, "config": parent_config})
        parent_chunks = parent_splitter._do_split(parent_doc_input)

        for p_idx, p_chunk in enumerate(parent_chunks):
            # 부모 ID 재정의 (계층 구조 명확화)
            parent_id = f"{doc_id}_parent_{p_idx}"
            
            # 3. 부모 청크 저장
            p_chunk.update_metadata(
                chunk_id=parent_id,
                part_index=p_idx,
                doc_level="parent",
                child_ids=[] # 나중에 채움
            )
            final_chunks.append(p_chunk)

            # 4. [Phase 2] 자식 청크 생성 (The Content)
            child_doc_input = Document(
                content=p_chunk.chunk_content,
                metadata={
                    **doc.metadata,
                    "config": config, # 원래 설정(작은 size) 사용
                    "parent_id": parent_id,  # 연결 고리
                    "section_context": p_chunk.metadata.get("semantic_type", "unknown") # 문맥 상속
                }
            )
            
            child_chunks = child_splitter._do_split(child_doc_input)
            
            child_ids_list = []
            for c_idx, c_chunk in enumerate(child_chunks):
                child_id = f"{parent_id}_child_{c_idx}"
                child_ids_list.append(child_id)
                
                c_chunk.update_metadata(
                    chunk_id=child_id,
                    part_index=c_idx,
                    doc_level="child"
                )
                final_chunks.append(c_chunk)
            
            # 부모에게 자식 목록 역참조 추가 (양방향 연결)
            p_chunk.metadata["child_ids"] = child_ids_list

        return final_chunks