from typing import Any, Dict
from ..interfaces.base_fetcher import BaseFetcher
from ..core.exceptions import ConnectorError
import sqlalchemy 

class DbFetcher(BaseFetcher):
    """(Tier 2) 'SQL DB'에서 'columns'를 선택하여 가져오는 일반 엔진."""
    component_name = "DbFetcher"
    
    def initialize(self, **kwargs):
        db_uri = kwargs.get("db_uri")
        if not db_uri:
            raise ConnectorError("DbFetcher requires 'db_uri'.")
        self.engine = sqlalchemy.create_engine(db_uri)

    def _do_fetch(self, target: str, query: Dict[str, Any]) -> Any:
        # target = 테이블 이름 (e.g., "users")
        # query = {'columns': ['name', 'email'], 'where': 'age > 18'} (가정)
        
        # ⭐️ 쿼리가 없으면 "SELECT *", 있으면 "SELECT name, email"
        columns = query.get("columns", ["*"]) 
        
        # ⭐️ 'query'를 사용하여 "멍청하지 않은" SQL 쿼리 생성
        # (주의: 실제 제품에서는 SQL Injection 방지 로직이 필수)
        sql_query = f"SELECT {', '.join(columns)} FROM {target}"
        
        if "where" in query:
            sql_query += f" WHERE {query['where']}"
            
        with self.engine.connect() as connection:
            result = connection.execute(sqlalchemy.text(sql_query))
            return [row._asdict() for row in result] # 👈 dict 리스트 반환