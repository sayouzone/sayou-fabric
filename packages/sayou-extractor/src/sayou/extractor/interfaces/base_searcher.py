from abc import abstractmethod
from typing import Any, Dict, List
from sayou.core.base_component import BaseComponent
from sayou.extractor.core.exceptions import SearchError

class BaseSearcher(BaseComponent):
    """
    (Tier 1) 'Vector' 또는 'Keyword'로 '유사도 검색(Search)'을
    수행하는 인터페이스. (Template Method)
    """
    component_name = "BaseSearcher"
    SUPPORTED_TYPES: List[str] = []

    def search(self, search_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """[공통 골격] 유사도 검색 실행"""
        search_type = search_request.get("type", "unknown")
        self._log(f"Performing search for type '{search_type}'...")
        try:
            if search_type not in self.SUPPORTED_TYPES:
                raise SearchError(f"Unsupported search type: '{search_type}'")
            return self._do_search(search_request)
        except Exception as e:
            raise SearchError(f"Search failed: {e}")

    @abstractmethod
    def _do_search(self, search_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """[구현 필수] (e.g., {"type": "vector_knn", "vector": [...]})"""
        raise NotImplementedError