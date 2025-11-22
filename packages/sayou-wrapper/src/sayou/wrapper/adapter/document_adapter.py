from typing import List, Dict, Any

from ..interfaces.base_adapter import BaseAdapter
from ..schemas.sayou_standard import WrapperOutput, SayouNode

class DocumentChunkAdapter(BaseAdapter):
    """
    (Tier 2) sayou-chunking의 결과(List[Chunk])를 SayouNode로 변환하는 표준 어댑터.
    """
    component_name = "DocumentChunkAdapter"
    SUPPORTED_TYPES = ['document_chunk']

    def _do_adapt(self, raw_data: List[Dict[str, Any]]) -> WrapperOutput:
        nodes = []
        
        self._log(raw_data)
        for chunk in raw_data:
            
            self._log(chunk)
            content = chunk.get("chunk_content", "")
            meta = chunk.get("metadata", {})
            
            # 1. ID 매핑 (Prefix 'sayou:doc:' 추가)
            # chunk_id 예시: "doc_123_part_0"
            raw_id = meta.get("chunk_id", "unknown")
            node_id = f"sayou:doc:{raw_id}"
            
            # 2. Node Class 결정 (Semantic Type 활용)
            sem_type = meta.get("semantic_type", "text")
            is_header = meta.get("is_header", False)

            if is_header:
                node_class = "sayou:Topic"      # 헤더는 토픽 노드
            elif sem_type == "table":
                node_class = "sayou:Table"      # 표는 테이블 노드
            elif sem_type == "code_block":
                node_class = "sayou:Code"       # 코드는 코드 노드
            else:
                node_class = "sayou:TextFragment" # 나머지는 일반 텍스트 노드

            # 3. Attributes 매핑 (사내 표준 Predicate Key 사용)
            attributes = {
                "schema:text": content,
                "sayou:semanticType": sem_type,
                "sayou:pageIndex": meta.get("page_num"),
                "sayou:partIndex": meta.get("part_index")
            }
            
            # 4. Relationships 매핑 (Parent ID가 있다면 연결)
            relationships = {}
            parent_id = meta.get("parent_id")
            if parent_id:
                # 부모 ID도 표준 포맷으로 변환
                std_parent_id = f"sayou:doc:{parent_id}"
                relationships["sayou:hasParent"] = [std_parent_id]
            
            # 5. 최종 노드 생성
            node = SayouNode(
                node_id=node_id,
                node_class=node_class,
                friendly_name=f"DOC_NODE [{sem_type}] {raw_id}",
                attributes=attributes,
                relationships=relationships
            )
            nodes.append(node)

        return WrapperOutput(nodes=nodes, metadata={"source_system": "sayou-chunking"})