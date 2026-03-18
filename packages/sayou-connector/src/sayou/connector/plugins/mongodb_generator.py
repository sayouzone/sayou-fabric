from typing import Iterator

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_generator import BaseGenerator


@register_component("generator")
class MongoDBGenerator(BaseGenerator):
    """
    MongoDB Task Generator.
    Iterates over specified 'collections' or a custom 'query' (find filter).
    """

    component_name = "MongoDBGenerator"
    SUPPORTED_TYPES = ["mongodb"]

    @classmethod
    def can_handle(cls, source: str) -> float:
        return 1.0 if "mongo" in source.lower() else 0.0

    def _do_generate(self, source: str, **kwargs) -> Iterator[SayouTask]:
        conn_args = kwargs.get("connection_args", {})
        collections = kwargs.get("collections", [])
        query = kwargs.get("query")

        if collections:
            for col in collections:
                yield SayouTask(
                    source_type="mongodb",
                    uri=f"{source}/{col}",
                    params={
                        "mode": "collection",
                        "target": col,
                        "connection_args": conn_args,
                        "query": query,
                    },
                )
        else:
            raise ValueError("[MongoDBGenerator] 'collections' list is required.")
