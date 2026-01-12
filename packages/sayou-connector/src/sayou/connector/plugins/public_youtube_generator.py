import re
from typing import Iterator

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_generator import BaseGenerator


@register_component("generator")
class YouTubeGenerator(BaseGenerator):
    """
    Parses YouTube URLs/IDs and generates tasks.
    Supports comma-separated inputs.
    """

    component_name = "YouTubeGenerator"
    SUPPORTED_TYPES = ["youtube"]

    @classmethod
    def can_handle(cls, source: str) -> float:
        return 1.0 if source.startswith("youtube://") else 0.0

    def _do_generate(self, source: str, **kwargs) -> Iterator[SayouTask]:
        """
        Input: "https://youtu.be/xyz123, youtube://abc456"
        Output: SayouTask(uri="youtube://xyz123")
        """
        raw_source = source.replace("youtube://", "")
        items = [item.strip() for item in raw_source.split(",")]

        for item in items:
            video_id = self._extract_video_id(item)
            if video_id:
                yield SayouTask(
                    uri=f"youtube://{video_id}",
                    source_type="youtube",
                    meta={
                        "source": "youtube",
                        "video_id": video_id,
                        "filename": f"youtube_{video_id}",
                    },
                )

    def _extract_video_id(self, url_or_id: str) -> str:
        if len(url_or_id) == 11 and re.match(r"^[a-zA-Z0-9_-]{11}$", url_or_id):
            return url_or_id

        patterns = [
            r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
            r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})",
            r"(?:embed\/)([0-9A-Za-z_-]{11})",
        ]

        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)

        return None
