from typing import Any, Dict

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
except ImportError:
    build = None


@register_component("fetcher")
class GoogleYoutubeFetcher(BaseFetcher):
    """
    Fetches detailed metadata of a YouTube video.
    Stores as JSON.
    """

    component_name = "GoogleYoutubeFetcher"
    SUPPORTED_TYPES = ["youtube"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if uri.startswith("youtube-video://") else 0.0

    def _do_fetch(self, task: SayouTask) -> Dict[str, Any]:
        token_path = task.params.get("token_path")
        video_id = task.params.get("video_id")

        creds = Credentials.from_authorized_user_file(token_path)
        service = build("youtube", "v3", credentials=creds)

        response = (
            service.videos().list(part="snippet,statistics", id=video_id).execute()
        )

        if not response.get("items"):
            self._log(f"Video {video_id} not found or deleted.", level="warning")
            return {}

        video_data = response["items"][0]
        snippet = video_data["snippet"]
        stats = video_data["statistics"]

        return {
            "content": video_data,
            "meta": {
                "source": "google_youtube",
                "file_id": video_id,
                "title": snippet.get("title", "Untitled"),
                "channel": snippet.get("channelTitle"),
                "tags": snippet.get("tags", []),
                "views": stats.get("viewCount"),
                "extension": ".json",
                "description_snippet": snippet.get("description", "")[:100],
            },
        }
