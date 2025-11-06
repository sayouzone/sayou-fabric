from abc import abstractmethod
from typing import Any, Dict, List
from sayou.core.base_component import BaseComponent
from sayou.extractor.core.exceptions import QueryError

class BaseQuerier(BaseComponent):
    """
    (Tier 1) 'SQL', 'Cypher' 등 '구조화된 언어'를
    실행(Query)하는 인터페이스. (Template Method)
    """
    component_name = "BaseQuerier"
    SUPPORTED_TYPES: List[str] = []

    def query(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """[공통 골격] 구조화된 쿼리 실행"""
        query_type = query.get("type", "unknown")
        self._log(f"Executing query for type '{query_type}'...")
        try:
            if query_type not in self.SUPPORTED_TYPES:
                raise QueryError(f"Unsupported query type: '{query_type}'")
            return self._do_query(query)
        except Exception as e:
            raise QueryError(f"Query failed: {e}")

    @abstractmethod
    def _do_query(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """[구현 필수] (e.g., {"type": "sql", "statement": "..."})"""
        raise NotImplementedError