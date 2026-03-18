from typing import Iterator

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_generator import BaseGenerator


@register_component("generator")
class MSSQLGenerator(BaseGenerator):
    """
    Standard MSSQL (SQL Server) Task Generator.
    """

    component_name = "MSSQLGenerator"
    SUPPORTED_TYPES = ["mssql", "sqlserver"]

    @classmethod
    def can_handle(cls, source: str) -> float:
        # mssql:// or sqlserver://
        return 1.0 if any(k in source.lower() for k in cls.SUPPORTED_TYPES) else 0.0

    def _do_generate(self, source: str, **kwargs) -> Iterator[SayouTask]:
        conn_args = kwargs.get("connection_args", {})
        tables = kwargs.get("tables", [])
        query = kwargs.get("query")

        if tables:
            for table in tables:
                yield SayouTask(
                    source_type="mssql",
                    uri=f"{source}/{table}",
                    params={
                        "mode": "table",
                        "target": table,
                        "connection_args": conn_args,
                    },
                )
        elif query:
            yield SayouTask(
                source_type="mssql",
                uri=f"{source}/custom_query",
                params={"mode": "query", "target": query, "connection_args": conn_args},
            )
        else:
            raise ValueError("[MSSQLGenerator] Provide 'tables' or 'query'.")
