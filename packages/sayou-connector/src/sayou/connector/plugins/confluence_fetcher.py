from typing import Any, Dict

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher

try:
    from atlassian import Confluence
except ImportError:
    Confluence = None


@register_component("fetcher")
class ConfluenceFetcher(BaseFetcher):
    """
    Fetches Confluence page content (HTML).
    """

    component_name = "ConfluenceFetcher"
    SUPPORTED_TYPES = ["confluence"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if uri.startswith("confluence-page://") else 0.0

    def _do_fetch(self, task: SayouTask) -> Dict[str, Any]:
        params = task.params
        confluence = Confluence(
            url=params["url"], username=params["username"], password=params["token"]
        )

        page_id = params["page_id"]
        page = confluence.get_page_by_id(page_id, expand="body.storage,version")

        title = page["title"]
        body_html = page["body"]["storage"]["value"]
        web_link = page["_links"]["base"] + page["_links"]["webui"]
        version = page["version"]["number"]
        last_updated = page["version"]["when"]
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <meta name="source" content="confluence">
    <meta name="page_id" content="{page_id}">
    <meta name="url" content="{web_link}">
    <meta name="updated" content="{last_updated}">
</head>
<body>
    <h1>{title}</h1>
    <hr>
    {body_html}
</body>
</html>"""

        return {
            "content": full_html,
            "meta": {
                "source": "confluence",
                "file_id": page_id,
                "title": title,
                "url": web_link,
                "extension": ".html",
            },
        }
