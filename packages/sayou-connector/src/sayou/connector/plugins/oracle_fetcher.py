import datetime
from typing import Any, Dict, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher

try:
    import oracledb
except ImportError:
    oracledb = None


@register_component("fetcher")
class OracleFetcher(BaseFetcher):
    """
    Standard Oracle Fetcher.
    Executes standard SQL queries via 'oracledb'.
    Includes driver-level optimization for LOBs.
    """

    component_name = "OracleFetcher"
    SUPPORTED_TYPES = ["oracle"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if uri.lower().startswith("oracle") else 0.0

    def _do_fetch(self, task: SayouTask) -> List[Dict[str, Any]]:
        if not oracledb:
            raise ImportError("Please install 'oracledb'.")

        params = task.params
        conn_args = params.get("connection_args", {})
        target = params.get("target")
        mode = params.get("mode", "query")

        dsn = (
            conn_args.get("dsn")
            or f"{conn_args.get('host')}:{conn_args.get('port')}/{conn_args.get('service_name')}"
        )

        with oracledb.connect(
            user=conn_args.get("user"), password=conn_args.get("password"), dsn=dsn
        ) as connection:

            connection.outputtypehandler = self._output_type_handler

            with connection.cursor() as cursor:
                sql = target
                if mode == "table":
                    sql = f"SELECT * FROM {target}"

                self._log(f"Executing: {sql[:60]}...")
                cursor.execute(sql)

                columns = [col[0].lower() for col in cursor.description]
                results = []

                while True:
                    rows = cursor.fetchmany(5000)
                    if not rows:
                        break

                    for row in rows:
                        results.append(dict(zip(columns, self._basic_type_map(row))))

                return results

    def _output_type_handler(self, cursor, name, default_type, size, precision, scale):
        """Technical optimization: Fetch LOBs directly."""
        if default_type == oracledb.CLOB:
            return cursor.var(oracledb.DB_TYPE_LONG, arraysize=cursor.arraysize)
        if default_type == oracledb.BLOB:
            return cursor.var(oracledb.DB_TYPE_RAW, arraysize=cursor.arraysize)

    def _basic_type_map(self, row: tuple) -> list:
        """JSON Serialization Safety Only."""
        processed = []
        for val in row:
            if isinstance(val, datetime.datetime):
                processed.append(val.isoformat())
            else:
                processed.append(val)
        return processed
