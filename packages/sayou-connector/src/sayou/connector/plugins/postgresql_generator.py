from typing import Iterator

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_generator import BaseGenerator


@register_component("generator")
class PostgresqlGenerator(BaseGenerator):
    """
    Standard PostgreSQL Task Generator.
    Generates tasks based on table lists or custom queries.
    """

    component_name = "PostgresGenerator"
    SUPPORTED_TYPES = ["postgres", "postgresql"]

    @classmethod
    def can_handle(cls, source: str) -> float:
        return 1.0 if any(k in source.lower() for k in cls.SUPPORTED_TYPES) else 0.0

    def _do_generate(self, source: str, **kwargs) -> Iterator[SayouTask]:
        """
        kwargs:
            - connection_args (dict): host, port, dbname, user, password
            - tables (list): List of table names to fetch
            - query (str): Custom SQL query
        """
        conn_args = kwargs.get("connection_args", {})
        tables = kwargs.get("tables", [])
        query = kwargs.get("query")

        # Case 1: Table List
        if tables:
            for table in tables:
                yield SayouTask(
                    source_type="postgres",
                    uri=f"{source}/{table}",
                    params={
                        "mode": "table",
                        "target": table,
                        "connection_args": conn_args,
                    },
                )

        # Case 2: Custom Query
        elif query:
            yield SayouTask(
                source_type="postgres",
                uri=f"{source}/custom_query",
                params={"mode": "query", "target": query, "connection_args": conn_args},
            )

        else:
            raise ValueError("[PostgresGenerator] Provide 'tables' list or 'query'.")
