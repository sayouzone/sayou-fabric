from datetime import datetime
from typing import Any, Dict

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher

try:
    from slack_sdk import WebClient
except ImportError:
    WebClient = None


@register_component("fetcher")
class SlackFetcher(BaseFetcher):
    """
    Fetches full message content, including THREAD replies.
    """

    component_name = "SlackFetcher"
    SUPPORTED_TYPES = ["slack"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if uri.startswith("slack-message://") else 0.0

    def _do_fetch(self, task: SayouTask) -> Dict[str, Any]:
        params = task.params
        client = WebClient(token=params["token"])

        channel_id = params["channel_id"]
        channel_name = params["channel_name"]
        ts = params["ts"]
        root_msg = params["message_data"]

        # 1. Thread Check (reply_count > 0 means thread exists)
        thread_content = ""
        if root_msg.get("reply_count", 0) > 0:
            try:
                # conversations_replies: Get thread messages
                replies_res = client.conversations_replies(channel=channel_id, ts=ts)
                replies = replies_res.get("messages", [])

                # First message is the original message, so skip it and process replies only
                for reply in replies[1:]:
                    user = reply.get("user", "Unknown")
                    text = reply.get("text", "")
                    thread_content += f"\n> **User({user}):** {text}\n"

            except Exception as e:
                self._log(f"Failed to fetch thread: {e}", level="warning")

        # 2. Formatting
        # Slack Timestamp(Unix) -> Readable Date
        dt = datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d %H:%M:%S")
        user_id = root_msg.get("user", "System")
        main_text = root_msg.get("text", "")

        formatted_md = f"""# Slack Message in #{channel_name}

**User:** {user_id}
**Time:** {dt}
**Link:** https://slack.com/archives/{channel_id}/p{ts.replace('.', '')}

---
{main_text}

---
### Thread Replies
{thread_content if thread_content else "(No replies)"}
"""

        return {
            "content": formatted_md,
            "meta": {
                "source": "slack",
                "file_id": f"{channel_name}_{ts}",
                "title": f"Slack_#{channel_name}_{dt}",
                "channel": channel_name,
                "author": user_id,
                "extension": ".md",
            },
        }
