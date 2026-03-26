from typing import Iterator

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_generator import BaseGenerator


# ---------------------------------------------------------
# Generator
# ---------------------------------------------------------
@register_component("generator")
class NaverSearchGenerator(BaseGenerator):
    """
    Naver Search Generator.
    Generates tasks based on keywords and target categories (blog, news, etc.).
    """

    component_name = "NaverSearchGenerator"
    SUPPORTED_TYPES = ["naver"]

    @classmethod
    def can_handle(cls, source: str) -> float:
        return 1.0 if "naver" in source.lower() else 0.0

    def _do_generate(self, source: str, **kwargs) -> Iterator[SayouTask]:
        """
        kwargs:
            - query (str): Search keyword (Required).
            - categories (list): ['blog', 'news', 'cafearticle'] (Default: blog).
            - auth (dict): {'client_id': '...', 'client_secret': '...'}
        """
        query = kwargs.get("query")
        categories = kwargs.get("categories", ["blog"])
        auth = kwargs.get("auth", {})

        if not query:
            raise ValueError("[NaverGenerator] 'query' is required.")

        for cat in categories:
            yield SayouTask(
                source_type="naver",
                uri=f"naver://{cat}/{query}",
                params={"category": cat, "query": query, "auth": auth},
            )
