from typing import Iterator

import feedparser
from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_generator import BaseGenerator


@register_component("generator")
class RssGenerator(BaseGenerator):
    """
    Parses an RSS feed URL and yields tasks for each entry.
    """

    component_name = "RssGenerator"
    SUPPORTED_TYPES = ["rss"]

    @classmethod
    def can_handle(cls, source: str) -> float:
        return 1.0 if source.startswith("rss://") else 0.0

    def _do_generate(self, source: str, **kwargs) -> Iterator[SayouTask]:
        feed_url = source.replace("rss://", "https://").replace(
            "https://https://", "https://"
        )

        self._log(f"📰 Parsing RSS Feed: {feed_url}")
        feed = feedparser.parse(feed_url)

        if feed.bozo:
            self._log(f"⚠️ RSS parsing warning: {feed.bozo_exception}", level="warning")

        limit = int(kwargs.get("limit", 10))
        entries = feed.entries[:limit]

        for entry in entries:
            yield SayouTask(
                uri=f"rss-item://{entry.link}",
                source_type="rss",
                params={
                    "entry_data": entry,
                    "feed_title": feed.feed.get("title", "Unknown Feed"),
                },
            )
