from typing import Any, Dict

import wikipediaapi
from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher


@register_component("fetcher")
class WikipediaFetcher(BaseFetcher):
    component_name = "WikipediaFetcher"
    SUPPORTED_TYPES = ["wikipedia"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if uri.startswith("wiki-page://") else 0.0

    def _do_fetch(self, task: SayouTask) -> Dict[str, Any]:
        title = task.params["page_title"]
        lang = task.params.get("lang", "ko")

        wiki = wikipediaapi.Wikipedia(
            user_agent="SayouFabric/0.3 (hello@sayou.zone)", language=lang
        )
        page = wiki.page(title)

        full_text = page.text

        return full_text
        # {
        #     "content": full_text,
        #     "meta": {
        #         "source": "wikipedia",
        #         "file_id": page.fullurl,
        #         "title": page.title,
        #         "summary": page.summary[0:200],
        #         "url": page.fullurl,
        #         "extension": ".txt",
        #     },
        # }
