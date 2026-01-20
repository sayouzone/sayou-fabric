from typing import Any, Dict

import trafilatura
from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher


@register_component("fetcher")
class TrafilaturaFetcher(BaseFetcher):
    component_name = "TrafilaturaFetcher"
    SUPPORTED_TYPES = ["trafilatura"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if uri.startswith("trafilatura-page://") else 0.0

    def _do_fetch(self, task: SayouTask) -> Dict[str, Any]:
        url = task.params["url"]

        # 1. Download
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            raise ValueError(f"Failed to download: {url}")

        # 2. Extract (returns None if failed)
        # include_comments=False, include_tables=True
        result_text = trafilatura.extract(
            downloaded,
            include_links=True,
            output_format="markdown",
        )

        if not result_text:
            result_text = "(Content extraction failed or empty page)"

        # Extract metadata (title, etc.)
        # etc. trafilatura.extract_metadata(downloaded)

        return result_text
        # {
        #     "content": result_text,
        #     "meta": {
        #         "source": "trafilatura",
        #         "file_id": url,
        #         "title": "Web Page",
        #         "url": url,
        #         "extension": ".md",
        #     },
        # }
