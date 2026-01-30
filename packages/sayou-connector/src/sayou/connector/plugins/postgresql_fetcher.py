import datetime
import decimal
import uuid
from typing import Any, Dict, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None


@register_component("fetcher")
class PostgresqlFetcher(BaseFetcher):
    """
    Standard PostgreSQL Fetcher.
    Uses 'psycopg2.extras.RealDictCursor' for cleaner data structure.
    Handles UUID, Decimal, and Date serialization.
    """

    component_name = "PostgresFetcher"
    SUPPORTED_TYPES = ["postgres", "postgresql"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if any(k in uri.lower() for k in cls.SUPPORTED_TYPES) else 0.0

    def _do_fetch(self, task: SayouTask) -> List[Dict[str, Any]]:
        if not psycopg2:
            raise ImportError("Please install 'psycopg2' or 'psycopg2-binary'.")

        params = task.params
        conn_args = params.get("connection_args", {})
        target = params.get("target")
        mode = params.get("mode", "query")

        try:
            with psycopg2.connect(
                dbname=conn_args.get("dbname"),
                user=conn_args.get("user"),
                password=conn_args.get("password"),
                host=conn_args.get("host"),
                port=conn_args.get("port", 5432),
            ) as conn:

                # RealDictCursor: Return a dict with column names as keys
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:

                    sql = target
                    if mode == "table":
                        sql = f"SELECT * FROM {target}"

                    self._log(f"Executing: {sql[:60]}...")
                    cursor.execute(sql)

                    results = []

                    # Batch Fetch
                    while True:
                        rows = cursor.fetchmany(5000)
                        if not rows:
                            break

                        for row in rows:
                            clean_row = self._sanitize_dict(dict(row))
                            results.append(clean_row)

                    return results

        except Exception as e:
            raise e

    def _sanitize_dict(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Minimal type conversion for JSON Serialization.
        (UUID -> str, Decimal -> float/str, Date -> str)
        """
        new_row = {}
        for k, v in row.items():
            # 1. UUID
            if isinstance(v, uuid.UUID):
                new_row[k] = str(v)
            # 2. Decimal
            elif isinstance(v, decimal.Decimal):
                new_row[k] = float(v)
            # 3. Date/Time
            elif isinstance(v, (datetime.date, datetime.datetime)):
                new_row[k] = v.isoformat()
            # 4. Others
            else:
                new_row[k] = v
        return new_row
