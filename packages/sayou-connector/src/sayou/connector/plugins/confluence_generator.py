from typing import Iterator

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_generator import BaseGenerator

try:
    from atlassian import Confluence
except ImportError:
    Confluence = None


@register_component("generator")
class ConfluenceGenerator(BaseGenerator):
    """
    Scans Confluence Spaces and Pages.
    """

    component_name = "ConfluenceGenerator"
    SUPPORTED_TYPES = ["confluence"]

    @classmethod
    def can_handle(cls, source: str) -> float:
        return 1.0 if source.startswith("confluence://") else 0.0

    def _do_generate(self, source: str, **kwargs) -> Iterator[SayouTask]:
        if not Confluence:
            raise ImportError("Please install atlassian-python-api")

        # 1. Connection info (kwargs required)
        url = kwargs.get("url")  # ex: https://my-company.atlassian.net
        username = kwargs.get("username")  # Email address
        token = kwargs.get("token")  # API token

        if not (url and username and token):
            raise ValueError("Confluence requires 'url', 'username', and 'token'.")

        confluence = Confluence(url=url, username=username, password=token)

        # 2. Target Space
        # source: confluence://DS (DS is Space Key)
        # If Space Key is not provided, scan all spaces (warning: many data)
        space_key = source.replace("confluence://", "").strip()

        limit = int(kwargs.get("limit", 10))
        count = 0

        self._log(f"Accessing Confluence. Space: {space_key or 'ALL'}")

        # 3. Page list (CQL: Confluence Query Language)
        if space_key:
            cql = f'space = "{space_key}" AND type = "page" ORDER BY created DESC'
        else:
            cql = 'type = "page" ORDER BY created DESC'

        # start=0, limit=limit
        results = confluence.cql(cql, limit=limit)

        if "results" not in results:
            self._log("No pages found or permission denied.", level="warning")
            return

        for page in results["results"]:
            page_id = page["content"]["id"]
            title = page["content"]["title"]

            yield SayouTask(
                uri=f"confluence-page://{page_id}",
                source_type="confluence",
                params={
                    "url": url,
                    "username": username,
                    "token": token,
                    "page_id": page_id,
                    "title": title,
                },
            )
            count += 1
