import os
import re
from typing import Any, Dict

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import safe_run

from .config import SayouConfig
from .exceptions import BrainError


class BaseBrainPipeline(BaseComponent):
    """
    Abstract base class for all Brain orchestrator pipelines.

    Provides:
    - Unified ``SayouConfig`` initialisation
    - Callback propagation to every registered sub-pipeline
    - ``_resolve_output_path()`` / ``_sanitize_filename()`` helpers
    - ``process()`` class-method facade (override ``ingest()`` in subclasses)
    """

    component_name = "BaseBrainPipeline"

    # Subclasses populate this in __init__ with their sub-pipeline instances.
    _sub_pipelines: Dict[str, Any] = {}

    def _init_config(
        self, config: Dict[str, Any], kwargs: Dict[str, Any]
    ) -> SayouConfig:
        """Merge constructor ``config`` dict and loose ``**kwargs`` into a SayouConfig."""
        full = config or {}
        full.update(kwargs)
        return SayouConfig(full)

    @safe_run(default_return=None)
    def initialize(self, config: Dict[str, Any] = None, **kwargs) -> None:
        """
        Propagate updated configuration to all registered sub-pipelines.

        Also re-registers any pending callbacks on each sub-pipeline so that
        observers added after construction are correctly forwarded.
        """
        if config:
            self.config._config.update(config)
        self.config._config.update(kwargs)

        cfg = self.config
        for name, pipeline in self._sub_pipelines.items():
            section = getattr(cfg, name, {})
            pipeline.initialize(**section)

        self._propagate_callbacks()
        self._log(f"{self.component_name} initialised.")

    def _propagate_callbacks(self) -> None:
        """Forward all registered callbacks to every sub-pipeline."""
        for pipeline in self._sub_pipelines.values():
            for cb in self._callbacks:
                pipeline.add_callback(cb)

    def add_callback(self, callback) -> None:
        """Register callback and immediately propagate to all sub-pipelines."""
        super().add_callback(callback)
        for pipeline in self._sub_pipelines.values():
            pipeline.add_callback(callback)

    # ------------------------------------------------------------------
    # Output path helpers
    # ------------------------------------------------------------------

    def _resolve_output_path(self, destination: str, packet: Any, index: int) -> str:
        """
        Generate a unique output file path from packet metadata.

        If ``destination`` already has a file extension, it is returned as-is
        (single-file mode).  Otherwise, a filename is derived from the packet's
        metadata fields and joined to the destination directory.
        """
        meta: Dict[str, Any] = {}

        if hasattr(packet, "task") and packet.task:
            meta.update(getattr(packet.task, "meta", {}) or {})

        payload = getattr(packet, "data", None) or getattr(packet, "content", None)
        if isinstance(payload, dict):
            meta.update(payload.get("meta", {}))
        elif hasattr(packet, "meta") and packet.meta:
            meta.update(packet.meta)

        raw_name = (
            meta.get("filename")
            or meta.get("subject")
            or meta.get("title")
            or meta.get("uid")
            or meta.get("file_id")
            or f"file_{index}"
        )

        safe_name = self._sanitize_filename(str(raw_name))

        if os.path.splitext(destination)[1]:
            return destination

        return os.path.join(destination, safe_name)

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        return re.sub(r'[<>:"/\\|?*]', "_", name).strip()
