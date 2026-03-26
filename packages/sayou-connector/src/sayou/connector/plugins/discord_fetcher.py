from typing import Any, Dict

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher


@register_component("fetcher")
class DiscordFetcher(BaseFetcher):
    component_name = "DiscordFetcher"
    SUPPORTED_TYPES = ["discord"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if uri.startswith("discord-message://") else 0.0

    def _do_fetch(self, task: SayouTask) -> Dict[str, Any]:
        msg = task.params["message_data"]
        channel_id = task.params["channel_id"]

        author = msg.get("author", {}).get("username", "Unknown")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")
        msg_id = msg.get("id")
        formatted_md = f"""# Discord Message

**Author:** {author}
**Time:** {timestamp}
**Channel ID:** {channel_id}

---
{content}
"""

        return {
            "content": formatted_md,
            "meta": {
                "source": "discord",
                "file_id": f"discord_{channel_id}_{msg_id}",
                "title": f"Discord_{author}_{msg_id}",
                "author": author,
                "extension": ".md",
            },
        }
