import os
from typing import Iterator

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_generator import BaseGenerator


@register_component("generator")
class ObsidianGenerator(BaseGenerator):
    """
    Recursively scans a local directory (Vault) for Markdown files.
    """

    component_name = "ObsidianGenerator"
    SUPPORTED_TYPES = ["obsidian"]

    @classmethod
    def can_handle(cls, source: str) -> float:
        return 1.0 if source.startswith("obsidian://") else 0.0

    def _do_generate(self, source: str, **kwargs) -> Iterator[SayouTask]:
        # source ex: obsidian:///Users/me/vault
        root_path = source.replace("obsidian://", "")

        if not os.path.exists(root_path):
            raise FileNotFoundError(f"Vault path not found: {root_path}")

        self._log(f"💎 Scanning Obsidian Vault: {root_path}")

        for root, _, files in os.walk(root_path):
            for file in files:
                if file.endswith(".md"):
                    full_path = os.path.join(root, file)

                    # Obsidian URI (Optional usage for deep linking)
                    # obsidian://open?path=...

                    yield SayouTask(
                        uri=f"obsidian-file://{full_path}",
                        source_type="obsidian",
                        params={"path": full_path},
                    )
