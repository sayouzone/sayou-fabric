from abc import abstractmethod
from typing import Any, Dict, List
from sayou.core.base_component import BaseComponent
from sayou.extractor.core.exceptions import RetrievalError

class BaseRetriever(BaseComponent):
    """
    (Tier 1) 'Key' 또는 'ID'를 기반으로 데이터를 '조회(Retrieve)'하는
    모든 Retriever의 인터페이스. (Template Method)
    """
    component_name = "BaseRetriever"
    SUPPORTED_TYPES: List[str] = []

    def retrieve(self, request: Dict[str, Any]) -> Any:
        """[공통 골격] Key 기반 조회 실행"""
        req_type = request.get("type", "unknown")
        self._log(f"Retrieving data for type '{req_type}'...")
        try:
            if req_type not in self.SUPPORTED_TYPES:
                raise RetrievalError(f"Unsupported retrieval type: '{req_type}'")
            return self._do_retrieve(request)
        except Exception as e:
            raise RetrievalError(f"Retrieval failed: {e}")

    @abstractmethod
    def _do_retrieve(self, request: Dict[str, Any]) -> Any:
        """[구현 필수] (e.g., {"type": "file_read", "filepath": "..."})"""
        raise NotImplementedError