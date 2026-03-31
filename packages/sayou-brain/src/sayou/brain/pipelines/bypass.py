from typing import Any, Dict, Iterator

from sayou.connector import ConnectorPipeline
from sayou.core.decorators import measure_time
from sayou.core.schemas import SayouPacket
from sayou.loader import LoaderPipeline

from ..core.base_brain import BaseBrainPipeline


class BypassPipeline(BaseBrainPipeline):
    """
    Zero-transformation migration pipeline.

    Moves raw data from a source to a destination without any parsing,
    refinement, or chunking.  The packet payload is written exactly as
    received from the Connector.

    Flow
    ────
    Connector → Loader  (direct, no intermediate stages)

    Use cases
    ─────────
    - Raw file backup / archiving (PDFs, images, binaries as-is)
    - Database record migration with no schema change
    - Log shipping to cold storage
    - Staging: collect raw data first, process later

    Comparison with TransferPipeline
    ─────────────────────────────────
    ``TransferPipeline`` optionally runs data through ``RefineryPipeline``
    before writing.  ``BypassPipeline`` makes no such option available —
    the connector output is written verbatim.  Use ``BypassPipeline`` when
    fidelity to the original payload is the only requirement.
    """

    component_name = "BypassPipeline"

    def __init__(
        self,
        extra_generators=None,
        extra_fetchers=None,
        extra_writers=None,
        config: Dict[str, Any] = None,
        **kwargs,
    ):
        super().__init__()

        self.config = self._init_config(config, kwargs)
        cfg = self.config

        self.connector = ConnectorPipeline(
            extra_generators=extra_generators,
            extra_fetchers=extra_fetchers,
            **cfg.connector,
        )
        self.loader = LoaderPipeline(
            extra_writers=extra_writers,
            **cfg.loader,
        )

        self._sub_pipelines = {
            "connector": self.connector,
            "loader": self.loader,
        }

        self.initialize(**kwargs)

    @classmethod
    def process(
        cls,
        source: str,
        destination: str,
        strategies: Dict[str, str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        One-line facade.

        Example::

            BypassPipeline.process(
                "s3://raw-bucket/logs/",
                destination="./archive/",
            )
        """
        return cls(**kwargs).ingest(source, destination, strategies, **kwargs)

    @measure_time
    def ingest(
        self,
        source: str,
        destination: str,
        strategies: Dict[str, str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Stream raw packets from source to destination without transformation.

        Args:
            source: Source URI or path.
            destination: Target directory or URI.  Required.
            strategies: Per-stage strategy overrides (keys: connector, loader).

        Returns:
            Stats dict with keys ``read``, ``written``, ``failed``.
        """
        if not destination:
            raise ValueError("BypassPipeline requires a destination.")

        self._emit("on_start", input_data={"source": source, "type": "bypass"})
        strategies = strategies or {}
        stats: Dict[str, int] = {"read": 0, "written": 0, "failed": 0}
        run_config = {**self.config._config, **kwargs}

        self._log(f"Bypass: {source} -> {destination}")

        # ── Phase 1: Extract ─────────────────────────────────────────
        try:
            packets: Iterator[SayouPacket] = self.connector.run(
                source,
                strategy=strategies.get("connector", "auto"),
                **run_config,
            )
            if not packets:
                self._log("No data returned by connector.", level="warning")
                return stats
        except Exception as exc:
            self._log(f"[Phase 1] Extraction failed: {exc}", level="error")
            self._emit("on_error", error=exc)
            return stats

        # ── Phase 2: Write verbatim ───────────────────────────────────
        for i, packet in enumerate(packets):
            if not packet.success:
                self._log(f"Packet error: {packet.error}", level="warning")
                stats["failed"] += 1
                continue

            stats["read"] += 1
            final_path = self._resolve_output_path(destination, packet, i)

            try:
                success = self.loader.run(
                    input_data=packet.data,
                    destination=final_path,
                    strategy=strategies.get("loader", "auto"),
                    **run_config,
                )
                if success:
                    stats["written"] += 1
                else:
                    self._log(f"Loader returned False for: {final_path}", level="error")
                    stats["failed"] += 1
            except Exception as exc:
                self._log(f"[Phase 2] Write error on item {i}: {exc}", level="error")
                stats["failed"] += 1

        self._emit("on_finish", result_data=stats, success=True)
        self._log(f"Bypass complete. {stats}")
        return stats
