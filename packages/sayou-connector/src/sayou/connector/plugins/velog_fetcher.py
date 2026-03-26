from typing import Any, Dict

import requests
from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher


@register_component("fetcher")
class VelogFetcher(BaseFetcher):
    component_name = "VelogFetcher"
    SUPPORTED_TYPES = ["velog"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if uri.startswith("velog-post://") else 0.0

    def _do_fetch(self, task: SayouTask) -> Dict[str, Any]:
        username = task.params["username"]
        slug = task.params["slug"]

        url = "https://v2.velog.io/graphql"
        query = """
        query Post($username: String, $slug: String) {
            post(username: $username, url_slug: $slug) {
                title
                body
                tags
            }
        }
        """

        variables = {"username": username, "slug": slug}

        response = requests.post(url, json={"query": query, "variables": variables})
        data = response.json()

        post_data = data.get("data", {}).get("post", {})
        if not post_data:
            raise ValueError(f"Post not found: {slug}")

        body = post_data["body"]
        tags = ", ".join(post_data.get("tags", []))

        final_content = f"""# {post_data['title']}

**Author:** {username}
**Date:** {task.params.get('date')}
**Tags:** {tags}
**Link:** https://velog.io/@{username}/{slug}

---
{body}
"""

        return {
            "content": final_content,
            "meta": {
                "source": "velog",
                "file_id": f"{username}_{slug}",
                "title": post_data["title"],
                "author": username,
                "extension": ".md",
            },
        }
