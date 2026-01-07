from typing import Iterator

import requests
from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_generator import BaseGenerator


@register_component("generator")
class NotionGenerator(BaseGenerator):
    """
    Discovers Notion pages accessible by the integration token.
    Supports:
    - notion://search : Find all pages
    - notion://page/{page_id} : Target specific page
    """

    component_name = "NotionGenerator"
    SUPPORTED_TYPES = ["notion"]

    def _do_generate(self, source: str, **kwargs) -> Iterator[SayouTask]:
        token = kwargs.get("notion_token")
        if not token:
            raise ValueError("Config 'notion_token' is required.")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

        if "notion://page/" in source:
            page_id = source.split("notion://page/")[-1]
            yield self._create_task(page_id, "Target Page", token)
            return

        if source == "notion://search":
            url = "https://api.notion.com/v1/search"
            payload = {"filter": {"value": "page", "property": "object"}}

            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                results = response.json().get("results", [])
                for page in results:
                    page_id = page["id"]
                    title = "Untitled"
                    props = page.get("properties", {})
                    for key, val in props.items():
                        if val.get("type") == "title":
                            titles = val.get("title", [])
                            if titles:
                                title = titles[0].get("plain_text", "")
                            break

                    yield self._create_task(page_id, title, token)
            else:
                raise RuntimeError(f"Notion Search Failed: {response.text}")

    def _create_task(self, page_id: str, title: str, token: str) -> SayouTask:
        return SayouTask(
            uri=f"notion://page/{page_id}",
            source_type="notion",
            params={
                "notion_token": token,
            },
            meta={
                "source": "notion",
                "page_id": page_id,
                "title": title,
                "filename": f"notion_{title}_{page_id[:8]}",
            },
        )
