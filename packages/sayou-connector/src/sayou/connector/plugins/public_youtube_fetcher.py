from typing import Any, Dict

import requests
from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None


@register_component("fetcher")
class YouTubeFetcher(BaseFetcher):
    """
    Fetches raw YouTube transcript and metadata.
    Returns a Dict containing 'transcript' (List) and 'video_meta' (Dict).
    """

    component_name = "YouTubeFetcher"
    SUPPORTED_TYPES = ["youtube"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if uri.startswith("youtube://") else 0.0

    def _do_fetch(self, task: SayouTask) -> Dict[str, Any]:
        if not YouTubeTranscriptApi:
            raise ImportError("Package 'youtube-transcript-api' is required.")

        video_id = task.meta.get("video_id")
        if not video_id:
            video_id = task.uri.replace("youtube://", "")

        video_meta = self._fetch_metadata(video_id)

        transcript_data = []
        try:
            yt_api = YouTubeTranscriptApi()
            transcript_list = yt_api.list(video_id)
            transcript = transcript_list.find_transcript(["ko", "en", "en-US", "ja"])
            transcript_data = transcript.fetch()

        except Exception as e:
            self._log(f"Transcript fetch failed for {video_id}: {e}", level="warning")
            transcript_data = []

        return {
            "content": transcript_data,
            "meta": {
                "source": "youtube",
                "video_id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                **video_meta,
            },
        }

    def _fetch_metadata(self, video_id: str) -> Dict[str, Any]:
        """
        Scrapes detailed metadata (Date, Views, Tags, Thumbnail) via requests.
        """
        url = f"https://www.youtube.com/watch?v={video_id}"
        info = {
            "title": f"YouTube_{video_id}",
            "author": "Unknown",
            "description": "",
            "publish_date": "",
            "view_count": 0,
            "keywords": [],
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
            "duration_seconds": 0,
        }

        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            if res.status_code == 200:
                html = res.text
                import re

                # 1. Title
                title_match = re.search(
                    r'<meta property="og:title" content="(.*?)">', html
                )
                if title_match:
                    info["title"] = title_match.group(1).replace(" - YouTube", "")

                # 2. Description
                desc_match = re.search(
                    r'<meta property="og:description" content="(.*?)">', html
                )
                if desc_match:
                    info["description"] = desc_match.group(1)

                # 3. Author (Channel Name)
                author_match = re.search(
                    r'<link itemprop="name" content="(.*?)">', html
                )
                if author_match:
                    info["author"] = author_match.group(1)

                # 4. Publish Date (ISO 8601 Format: YYYY-MM-DD)
                date_match = re.search(
                    r'<meta itemprop="datePublished" content="(.*?)">', html
                )
                if date_match:
                    info["publish_date"] = date_match.group(1)

                # 5. View Count (InteractionCount)
                views_match = re.search(
                    r'<meta itemprop="interactionCount" content="(\d+)">', html
                )
                if views_match:
                    info["view_count"] = int(views_match.group(1))

                # 6. Keywords (Tags)
                tags_match = re.search(r'<meta name="keywords" content="(.*?)">', html)
                if tags_match:
                    info["keywords"] = [
                        tag.strip() for tag in tags_match.group(1).split(",")
                    ]

                # 7. Duration (ISO 8601 Duration: PT1H30M...)
                dur_match = re.search(
                    r'<meta itemprop="duration" content="(.*?)">', html
                )
                if dur_match:
                    info["duration_iso"] = dur_match.group(1)

        except Exception as e:
            self._log(f"Meta scraping warning: {e}", level="debug")

        return info
