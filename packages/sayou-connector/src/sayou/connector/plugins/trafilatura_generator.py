from typing import Iterator

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_generator import BaseGenerator


@register_component("generator")
class TrafilaturaGenerator(BaseGenerator):
    """
    Simple generator that takes a URL (or list of URLs via kwargs) and passes them to fetcher.
    """

    component_name = "TrafilaturaGenerator"
    SUPPORTED_TYPES = ["trafilatura"]

    @classmethod
    def can_handle(cls, source: str) -> float:
        return 1.0 if source.startswith("trafilatura://") else 0.0

    def _do_generate(self, source: str, **kwargs) -> Iterator[SayouTask]:
        real_url = source.replace("trafilatura://", "")

        if not real_url.startswith("http"):
            real_url = f"https://{real_url}"

        yield SayouTask(
            uri=f"trafilatura-page://{real_url}",
            source_type="trafilatura",
            params={"url": real_url},
        )
