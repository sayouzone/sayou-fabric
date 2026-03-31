import os
from typing import Any, Dict

from sayou.connector import ConnectorPipeline
from sayou.core.decorators import measure_time
from sayou.loader import LoaderPipeline
from sayou.refinery import RefineryPipeline

from ..core.base_brain import BaseBrainPipeline


class TransferPipeline(BaseBrainPipeline):
    """
    Lightweight ETL pipeline.

    Moves data from a source to a destination with minimal transformation.

    Flow
    ────
    Connector → [Refinery] → Loader

    Use cases
    ─────────
    - Database migration
    - Log backup
    - Raw data archiving
    """

    component_name = "TransferPipeline"

    def __init__(
        self,
        extra_generators=None,
        extra_fetchers=None,
        extra_normalizers=None,
        extra_processors=None,
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
        self.refinery = RefineryPipeline(
            extra_normalizers=extra_normalizers,
            extra_processors=extra_processors,
            **cfg.refinery,
        )
        self.loader = LoaderPipeline(
            extra_writers=extra_writers,
            **cfg.loader,
        )

        self._sub_pipelines = {
            "connector": self.connector,
            "refinery": self.refinery,
            "loader": self.loader,
        }

        self.initialize(**kwargs)

    @classmethod
    def process(
        cls,
        source: str,
        destination: str = None,
        strategies: Dict[str, str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        One-line facade.

        Example::

            TransferPipeline.process(
                "https://example.com/data",
                destination="./output/",
            )
        """
        return cls(**kwargs).ingest(source, destination, strategies, **kwargs)

    @measure_time
    def ingest(
        self,
        source: str,
        destination: str = None,
        strategies: Dict[str, str] = None,
        use_refinery: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Execute the transfer pipeline.

        Args:
            source: Source URI or path.
            destination: Target directory.  Required.
            strategies: Per-stage strategy overrides (keys: connector, refinery, loader).
            use_refinery: When True, raw data passes through RefineryPipeline before
                          being written.  Default False for zero-copy mode.
        """
        self._emit("on_start", input_data={"source": source, "type": "transfer"})
        strategies = strategies or {}
        stats: Dict[str, int] = {"read": 0, "written": 0, "failed": 0}

        # ── Prep ──────────────────────────────────────────────────────
        if not destination:
            raise ValueError("TransferPipeline requires a destination directory.")

        os.makedirs(destination, exist_ok=True)
        run_config = {**self.config._config, **kwargs}
        self._log(f"Transfer: {source} -> {destination}")

        # ── Phase 1: Extract ─────────────────────────────────────────
        try:
            packets_gen = self.connector.run(
                source,
                strategy=strategies.get("connector", "auto"),
                **run_config,
            )
            if not packets_gen:
                self._log("No data returned by connector.", level="warning")
                return stats
        except Exception as exc:
            self._log(f"[Phase 1] Extraction failed: {exc}", level="error")
            self._emit("on_error", error=exc)
            return stats

        # ── Phase 2: Transform & Load (streaming) ────────────────────
        for i, packet in enumerate(packets_gen):
            if not packet.success:
                self._log(f"Packet error: {packet.error}", level="warning")
                stats["failed"] += 1
                continue

            stats["read"] += 1
            current_data = packet.data

            if use_refinery:
                try:
                    processed = self.refinery.run(
                        current_data,
                        strategy=strategies.get("refinery", "auto"),
                        **run_config,
                    )
                    if processed:
                        current_data = processed
                    else:
                        self._log(f"Refinery filtered item {i}.", level="warning")
                        continue
                except Exception as exc:
                    self._log(
                        f"[Phase 2] Refinery error on item {i}: {exc}", level="error"
                    )
                    stats["failed"] += 1
                    continue

            final_path = self._resolve_output_path(destination, packet, i)

            try:
                success = self.loader.run(
                    input_data=current_data,
                    destination=final_path,
                    strategy=strategies.get("loader", "auto"),
                    **run_config,
                )
                if success:
                    stats["written"] += 1
                    self._log(f"Saved: {os.path.basename(final_path)}")
                else:
                    self._log(f"Save returned False: {final_path}", level="error")
                    stats["failed"] += 1
            except Exception as exc:
                self._log(f"[Phase 2] Load error: {exc}", level="error")
                stats["failed"] += 1

        self._emit("on_finish", result_data=stats, success=True)
        self._log(f"Transfer complete. {stats}")
        return stats
