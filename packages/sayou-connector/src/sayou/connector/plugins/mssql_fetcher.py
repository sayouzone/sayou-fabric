import datetime
import decimal
import uuid
from typing import Any, Dict, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher

try:
    import pymssql
except ImportError:
    pymysql = None


@register_component("fetcher")
class MSSQLFetcher(BaseFetcher):
    """
    Standard MSSQL Fetcher.
    Uses 'pymssql'.
    """

    component_name = "MSSQLFetcher"
    SUPPORTED_TYPES = ["mssql", "sqlserver"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if any(k in uri.lower() for k in cls.SUPPORTED_TYPES) else 0.0

    def _do_fetch(self, task: SayouTask) -> List[Dict[str, Any]]:
        if not pymssql:
            raise ImportError("Please install 'pymssql'.")

        params = task.params
        conn_args = params.get("connection_args", {})
        target = params.get("target")
        mode = params.get("mode", "query")

        # Connection
        # pymssql takes server, user, password, and database arguments.
        connection = pymssql.connect(
            server=conn_args.get("host") or conn_args.get("server"),
            port=int(conn_args.get("port", 1433)),
            user=conn_args.get("user"),
            password=conn_args.get("password"),
            database=conn_args.get("database") or conn_args.get("dbname"),
            as_dict=True,
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
                        results.append(self._sanitize_mssql_types(row))

                return results
        finally:
            connection.close()

    def _sanitize_mssql_types(self, row: Dict[str, Any]) -> Dict[str, Any]:
        new_row = {}
        for k, v in row.items():
            if isinstance(v, (datetime.date, datetime.datetime)):
                new_row[k] = v.isoformat()
            elif isinstance(v, decimal.Decimal):
                new_row[k] = float(v)
            elif isinstance(v, uuid.UUID):
                new_row[k] = str(v)
            else:
                new_row[k] = v
        return new_row
