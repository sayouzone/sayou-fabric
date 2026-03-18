import datetime
import decimal
from typing import Any, Dict, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher

try:
    import pymysql
    import pymysql.cursors
except ImportError:
    pymysql = None


@register_component("fetcher")
class MySQLFetcher(BaseFetcher):
    """
    Standard MySQL Fetcher.
    Uses 'pymysql' (Pure Python).
    """

    component_name = "MySQLFetcher"
    SUPPORTED_TYPES = ["mysql", "mariadb"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if any(k in uri.lower() for k in cls.SUPPORTED_TYPES) else 0.0

    def _do_fetch(self, task: SayouTask) -> List[Dict[str, Any]]:
        if not pymysql:
            raise ImportError("Please install 'pymysql'.")

        params = task.params
        conn_args = params.get("connection_args", {})
        target = params.get("target")
        mode = params.get("mode", "query")

        # Connection
        connection = pymysql.connect(
            host=conn_args.get("host"),
            port=conn_args.get("port", 3306),
            user=conn_args.get("user"),
            password=conn_args.get("password"),
            database=conn_args.get("database") or conn_args.get("dbname"),
            charset=conn_args.get("charset", "utf8mb4"),
            cursorclass=pymysql.cursors.DictCursor,
        )

        try:
            with connection.cursor() as cursor:
                sql = target
                if mode == "table":
                    sql = f"SELECT * FROM {target}"

                self._log(f"Executing: {sql[:60]}...")
                cursor.execute(sql)

                results = []
                while True:
                    rows = cursor.fetchmany(5000)
                    if not rows:
                        break
                    for row in rows:
                        results.append(self._sanitize_mysql_types(row))

                return results
        finally:
            connection.close()

    def _sanitize_mysql_types(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Handling JSON incompatible types"""
        new_row = {}
        for k, v in row.items():
            if isinstance(v, (datetime.date, datetime.datetime)):
                new_row[k] = v.isoformat()
            elif isinstance(v, decimal.Decimal):
                new_row[k] = float(v)
            elif isinstance(v, bytes):
                try:
                    new_row[k] = v.decode("utf-8")
                except:
                    new_row[k] = str(v)
            else:
                new_row[k] = v
        return new_row
