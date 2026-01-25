from typing import Any, Dict

import trafilatura
from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher


@register_component("fetcher")
class RssFetcher(BaseFetcher):
    component_name = "RssFetcher"
    SUPPORTED_TYPES = ["rss"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if uri.startswith("rss-item://") else 0.0

    def _do_fetch(self, task: SayouTask) -> Dict[str, Any]:
        entry = task.params["entry_data"]
        feed_title = task.params.get("feed_title", "")

        # 1. Extract RSS entry data
        title = entry.get("title", "No Title")
        link = entry.get("link", "")
        author = entry.get("author", "Unknown")
        published = entry.get("published", "")

        raw_summary = ""
        if "content" in entry:
            raw_summary = entry.content[0].value
        elif "summary" in entry:
            raw_summary = entry.summary
        else:
            raw_summary = entry.get("description", "")

        # 2. Full-Text Extraction
        full_text = ""
        if link and link.startswith("http"):
            try:
                downloaded = trafilatura.fetch_url(link)
                if downloaded:
                    full_text = trafilatura.extract(
                        downloaded, output_format="markdown"
                    )
            except Exception as e:
                self._log(f"Failed to crawl {link}: {e}", level="warning")

        final_content = full_text if full_text else raw_summary

        formatted_content = f"""# {title}

**Source:** {feed_title}
**Author:** {author}
**Date:** {published}
**Link:** {link}

---
{final_content}
"""
        return formatted_content
        # {
        #     "content": formatted_content,
        #     "meta": {
        #         "source": "rss",
        #         "file_id": link,
        #         "title": title,
        #         "author": author,
        #         "published": published,
        #         "feed_name": feed_title,
        #         "extension": ".md"
        #     }
        # }
