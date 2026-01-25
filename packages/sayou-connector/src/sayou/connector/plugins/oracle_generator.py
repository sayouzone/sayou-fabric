from typing import Iterator

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_generator import BaseGenerator


@register_component("generator")
class OracleGenerator(BaseGenerator):
    """
    Standard Oracle Task Generator.
    Simply generates tasks for each table provided.
    No custom business logic (like date splitting).
    """

    component_name = "OracleGenerator"
    SUPPORTED_TYPES = ["oracle"]

    @classmethod
    def can_handle(cls, source: str) -> float:
        return 1.0 if source.lower().startswith("oracle") else 0.0

    def _do_generate(self, source: str, **kwargs) -> Iterator[SayouTask]:
        """
        Input: List of table names or a specific query.
        Output: SayouTask for each target.
        """
        conn_args = kwargs.get("connection_args", {})
        tables = kwargs.get("tables", [])
        query = kwargs.get("query")

        if tables:
            for table in tables:
                yield SayouTask(
                    source_type="oracle",
                    uri=f"{source}/{table}",
                    params={
                        "mode": "table",
                        "target": table,
                        "connection_args": conn_args,
                    },
                )

        elif query:
            yield SayouTask(
                source_type="oracle",
                uri=f"{source}/custom_query",
                params={
                    "mode": "query",
                    "target": query,
                    "connection_args": conn_args,
                },
            )

        else:
            raise ValueError(
                "[OracleGenerator] Either 'tables' or 'query' must be provided."
            )
