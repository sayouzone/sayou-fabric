from typing import Iterator

import requests
from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_generator import BaseGenerator


@register_component("generator")
class DiscordGenerator(BaseGenerator):
    """
    Scans a Discord Channel for messages using REST API.
    """

    component_name = "DiscordGenerator"
    SUPPORTED_TYPES = ["discord"]

    @classmethod
    def can_handle(cls, source: str) -> float:
        return 1.0 if source.startswith("discord://") else 0.0

    def _do_generate(self, source: str, **kwargs) -> Iterator[SayouTask]:
        # source: discord://1234567890 (Channel ID)
        channel_id = source.replace("discord://", "").strip()

        token = kwargs.get("token")
        if not token:
            raise ValueError("Discord Bot Token is required.")

        limit = int(kwargs.get("limit", 20))

        headers = {"Authorization": f"Bot {token}"}
        url = (
            f"https://discord.com/api/v10/channels/{channel_id}/messages?limit={limit}"
        )

        self._log(f"🎮 Accessing Discord Channel ID: {channel_id}")

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            self._log(f"Discord API Error: {response.text}", level="error")
            return

        messages = response.json()

        for msg in messages:
            if not msg.get("content"):
                continue

            yield SayouTask(
                uri=f"discord-message://{channel_id}/{msg['id']}",
                source_type="discord",
                params={"token": token, "channel_id": channel_id, "message_data": msg},
            )
