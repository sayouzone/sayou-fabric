from typing import Iterator

import wikipediaapi
from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_generator import BaseGenerator


@register_component("generator")
class WikipediaGenerator(BaseGenerator):
    """
    Searches Wikipedia and generates tasks for pages.
    """

    component_name = "WikipediaGenerator"
    SUPPORTED_TYPES = ["wikipedia"]

    @classmethod
    def can_handle(cls, source: str) -> float:
        return 1.0 if source.startswith("wiki://") else 0.0

    def _do_generate(self, source: str, **kwargs) -> Iterator[SayouTask]:
        topic = source.replace("wiki://", "")
        lang = kwargs.get("lang", "ko")

        wiki = wikipediaapi.Wikipedia(
            user_agent="SayouFabric/0.3 (connect@sayouzone.com)", language=lang
        )

        page = wiki.page(topic)

        if page.exists():
            yield SayouTask(
                uri=f"wiki-page://{page.title}",
                source_type="wikipedia",
                params={"page_title": page.title, "lang": lang},
            )
        else:
            self._log(
                f"Topic '{topic}' not found directly. (Search not implemented in simple generator)",
                level="warning",
            )
