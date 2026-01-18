from typing import Iterator

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_generator import BaseGenerator

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
except ImportError:
    build = None


@register_component("generator")
class GoogleYoutubeGenerator(BaseGenerator):
    """
    Scans user's YouTube library (Liked videos, Playlists).
    Yields tasks for individual video metadata fetching.
    """

    component_name = "GoogleYoutubeGenerator"
    SUPPORTED_TYPES = ["youtube"]

    @classmethod
    def can_handle(cls, source: str) -> float:
        return 1.0 if source.startswith("youtube://") else 0.0

    def _do_generate(self, source: str, **kwargs) -> Iterator[SayouTask]:
        token_path = kwargs.get("token_path") or kwargs.get("google_token_path")
        if not token_path:
            raise ValueError("[GoogleYoutubeGenerator] 'token_path' is required.")

        # target: 'liked' or 'uploads' or specific playlist_id
        target = kwargs.get("target", "liked")
        max_results = int(kwargs.get("limit", 20))

        creds = Credentials.from_authorized_user_file(token_path)
        service = build("youtube", "v3", credentials=creds)

        self._log(f"📺 Scanning YouTube target: {target}...")

        video_ids = []

        try:
            if target == "liked":
                request = service.videos().list(
                    part="id,snippet", myRating="like", maxResults=max_results
                )
                response = request.execute()
                for item in response.get("items", []):
                    video_ids.append(item["id"])

            elif target == "uploads":
                channels_resp = (
                    service.channels().list(mine=True, part="contentDetails").execute()
                )
                if not channels_resp["items"]:
                    self._log("No channel found for this user.")
                    return

                uploads_playlist_id = channels_resp["items"][0]["contentDetails"][
                    "relatedPlaylists"
                ]["uploads"]

                pl_request = service.playlistItems().list(
                    part="contentDetails",
                    playlistId=uploads_playlist_id,
                    maxResults=max_results,
                )
                pl_response = pl_request.execute()
                for item in pl_response.get("items", []):
                    video_ids.append(item["contentDetails"]["videoId"])

            self._log(f"📺 Found {len(video_ids)} videos. Generating tasks...")

            for vid in video_ids:
                yield SayouTask(
                    uri=f"youtube-video://{vid}",
                    source_type="youtube",
                    params={"token_path": token_path, "video_id": vid},
                )

        except Exception as e:
            self._log(f"YouTube Generator failed: {e}", level="error")
            raise e
