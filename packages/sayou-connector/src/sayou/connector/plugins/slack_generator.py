from typing import Iterator

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_generator import BaseGenerator

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
except ImportError:
    WebClient = None


@register_component("generator")
class SlackGenerator(BaseGenerator):
    """
    Scans a Slack Channel for message history.
    """

    component_name = "SlackGenerator"
    SUPPORTED_TYPES = ["slack"]

    @classmethod
    def can_handle(cls, source: str) -> float:
        return 1.0 if source.startswith("slack://") else 0.0

    def _do_generate(self, source: str, **kwargs) -> Iterator[SayouTask]:
        if not WebClient:
            raise ImportError("Please install slack_sdk")

        token = kwargs.get("token")
        if not token:
            raise ValueError("Slack Bot Token (xoxb-...) is required.")

        client = WebClient(token=token)

        # source: slack://general -> channel_name: general
        channel_name = source.replace("slack://", "").strip("#")

        self._log(f"Accessing Slack channel: #{channel_name}")

        # 1. Channel Name -> Channel ID (Slack API requires ID)
        channel_id = self._find_channel_id(client, channel_name)
        if not channel_id:
            self._log(f"Channel '#{channel_name}' not found.", level="warning")
            return

        # 2. Message History
        limit = int(kwargs.get("limit", 20))

        try:
            # conversations_history: Get main messages from the channel
            result = client.conversations_history(channel=channel_id, limit=limit)
            messages = result.get("messages", [])

            for msg in messages:
                # Bot messages or system messages filtering
                ts = msg.get("ts")
                text = msg.get("text", "")

                yield SayouTask(
                    uri=f"slack-message://{channel_id}/{ts}",
                    source_type="slack",
                    params={
                        "token": token,
                        "channel_id": channel_id,
                        "channel_name": channel_name,
                        "message_data": msg,
                        "ts": ts,
                    },
                )

        except SlackApiError as e:
            self._log(f"Slack API Error: {e.response['error']}", level="error")

    def _find_channel_id(self, client, name):
        """Find channel ID by name (Simple version without Paginator)"""
        try:
            # types: public_channel, private_channel
            response = client.conversations_list(types="public_channel,private_channel")
            for channel in response["channels"]:
                if channel["name"] == name:
                    return channel["id"]
        except Exception:
            pass
        return None
