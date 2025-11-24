import sqlite3

from ..core.models import FetchTask, FetchResult
from ..interfaces.base_fetcher import BaseFetcher

class SqliteFetcher(BaseFetcher):
    """
    (Tier 2) SQLite DB 파일에서 쿼리를 실행합니다.
    """
    component_name = "SqliteFetcher"
    SUPPORTED_TYPES = ["sqlite"]

    def fetch(self, task: FetchTask) -> FetchResult:
        db_path = task.uri
        query = task.params.get("query")
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(query)
            rows = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            return FetchResult(task=task, data=rows, success=True)
            
        except Exception as e:
            return FetchResult(task=task, data=None, success=False, error=str(e))