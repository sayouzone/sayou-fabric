from typing import Any, Dict, List
from sayou.extractor.interfaces.base_querier import BaseQuerier
from sayou.extractor.core.exceptions import QueryError, ExtractorError

try: import sqlalchemy
except ImportError: sqlalchemy = None 

class SqlQuerier(BaseQuerier):
    """(Tier 2) 'SQL' 쿼리를 실행하는 일반 엔진."""
    component_name = "SqlQuerier"
    SUPPORTED_TYPES = ["sql"] # 👈 "sql" 처리

    def initialize(self, **kwargs):
        if not sqlalchemy:
            raise ExtractorError("SqlQuerier requires 'sqlalchemy'.")
        db_uri = kwargs.get("db_uri")
        if not db_uri:
            raise ExtractorError("SqlQuerier requires 'db_uri'.")
        self.engine = sqlalchemy.create_engine(db_uri)

    def _do_query(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """[Tier 1 구현] SQL 쿼리 실행"""
        statement = query.get("statement")
        params = query.get("params", {})
        if not statement:
            raise QueryError("'sql' query requires a 'statement' field.")
            
        with self.engine.connect() as conn:
            result = conn.execute(sqlalchemy.text(statement), params)
            return [row._asdict() for row in result]