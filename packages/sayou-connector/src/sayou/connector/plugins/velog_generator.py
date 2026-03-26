from typing import Iterator

import requests
from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_generator import BaseGenerator


@register_component("generator")
class VelogGenerator(BaseGenerator):
    """
    Scans Velog posts for a specific user via GraphQL.
    """

    component_name = "VelogGenerator"
    SUPPORTED_TYPES = ["velog"]

    @classmethod
    def can_handle(cls, source: str) -> float:
        return 1.0 if source.startswith("velog://") else 0.0

    def _do_generate(self, source: str, **kwargs) -> Iterator[SayouTask]:
        username = source.replace("velog://", "").strip()
        limit = int(kwargs.get("limit", 10))

        url = "https://v2.velog.io/graphql"
        query = """
        query Posts($username: String, $limit: Int) {
            posts(username: $username, limit: $limit) {
                id
                title
                url_slug
                released_at
                short_description
            }
        }
        """

        variables = {"username": username, "limit": limit}

        try:
            response = requests.post(url, json={"query": query, "variables": variables})
            data = response.json()

            if "errors" in data:
                self._log(f"Velog GraphQL Error: {data['errors']}", level="warning")
                return

            posts = data.get("data", {}).get("posts", [])
            if not posts:
                self._log(f"No posts found for user: {username}", level="warning")
                return

            self._log(f"📝 Found {len(posts)} posts from Velog @{username}")

            for post in posts:
                slug = post["url_slug"]

                yield SayouTask(
                    uri=f"velog-post://{username}/{slug}",
                    source_type="velog",
                    params={
                        "username": username,
                        "slug": slug,
                        "title": post["title"],
                        "summary": post["short_description"],
                        "date": post["released_at"],
                    },
                )

        except Exception as e:
            self._log(f"Failed to query Velog: {e}", level="error")
