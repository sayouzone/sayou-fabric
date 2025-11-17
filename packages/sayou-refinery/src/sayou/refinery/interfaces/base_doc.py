from abc import abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
from sayou.core.base_component import BaseComponent

@dataclass
class ContentBlock:
    """
    Refinery가 Document를 정제한 후의 표준 출력.
    Chunker가 이 블록을 받아 청킹을 수행합니다.
    """
    type: str
    content: str
    metadata: Dict[str, Any]

class BaseDocRefiner(BaseComponent):
    """
    (Tier 1) 'Document'의 '직렬화된 데이터(Dict)'를
    'ContentBlock' 리스트로 정제(Refine)하는 인터페이스.
    """
    component_name = "BaseDocRefiner"

    @abstractmethod
    def refine(self, doc_data: Dict[str, Any]) -> List[ContentBlock]:
        """
        [구현 필수] Document 딕셔너리를 ContentBlock 리스트로 변환합니다.
        
        :param doc_data: sayou-document가 생성한 Document의 .model_dump() 결과(Dict)
        :return: 정제/변환된 ContentBlock 리스트
        """
        raise NotImplementedError