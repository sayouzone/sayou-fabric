import os
import time
from typing import Any, Dict

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher


@register_component("fetcher")
class ObsidianFetcher(BaseFetcher):
    component_name = "ObsidianFetcher"
    SUPPORTED_TYPES = ["obsidian"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if uri.startswith("obsidian-file://") else 0.0

    def _do_fetch(self, task: SayouTask) -> Dict[str, Any]:
        file_path = task.params["path"]

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        stat = os.stat(file_path)
        filename = os.path.basename(file_path)

        return content
        # {
        #     "content": content,
        #     "meta": {
        #         "source": "obsidian",
        #         "file_id": file_path,
        #         "title": os.path.splitext(filename)[0],
        #         "extension": ".md",
        #         "created_at": time.ctime(stat.st_ctime),
        #         "modified_at": time.ctime(stat.st_mtime),
        #     },
        # }
