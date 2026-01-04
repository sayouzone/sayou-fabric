import os
import traceback
from typing import Any, Dict

from sayou.connector import ConnectorPipeline
from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time, safe_run
from sayou.loader import LoaderPipeline
from sayou.refinery import RefineryPipeline

from ..core.config import SayouConfig


class TransferPipeline(BaseComponent):
    """
    (Tier 1) Lightweight ETL Pipeline.

    Purpose: Move data from Source to Destination with minimal transformation.
    Flow: Connector -> [Refinery] -> Loader
    Ideal for: DB Migration, Log Backup, Raw Data Archiving.
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
        """
        Initializes the Brain. Plugins are passed directly to sub-pipelines.
        """
        super().__init__()

        full_config = config or {}
        full_config.update(kwargs)
        self.config = SayouConfig(full_config)
        cfg = self.config

        # 1. Initialize Sub-pipelines
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
        [Facade] 1-Line Execution.

        Usage:
            TransferPipeline.process(
                "https://...",
                destination="./output.json",
            )
        """
        instance = cls(**kwargs)
        return instance.ingest(source, destination, strategies, **kwargs)

    @safe_run(default_return=None)
    def initialize(self, config: Dict[str, Any] = None, **kwargs):
        """
        [Transfer] Initialize all sub-pipelines with new configurations.

        This allows re-configuring the pipeline without recreating it.
        """
        if config:
            self.config._config.update(config)
        self.config._config.update(kwargs)

        cfg = self.config

        self.connector.initialize(**cfg.connector)
        self.refinery.initialize(**cfg.refinery)
        self.loader.initialize(**cfg.loader)

        self._log("TransferPipeline initialized. Configs propagated.")

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
        Execute the Transfer(ETL) pipeline with comprehensive error handling.
        """
        self._emit("on_start", input_data={"source": source, "type": "transfer"})
        strategies = strategies or {}
        stats = {"read": 0, "written": 0, "failed": 0}

        # -----------------------------------------------------------
        # [Prep] Configuration
        # -----------------------------------------------------------
        try:
            if not destination:
                raise ValueError("Destination is required for TransferPipeline.")

            run_config = {**self.config._config, **kwargs}
            self._log(f"--- Starting Transfer: {source} -> {destination} ---")

            if hasattr(self, "_callbacks"):
                for cb in self._callbacks:
                    self.connector.add_callback(cb)
                    self.refinery.add_callback(cb)
                    self.loader.add_callback(cb)

        except Exception as e:
            self._log(f"💥 [Prep] Config Error: {e}", level="error")
            self._emit("on_error", error=e)
            return stats

        # -----------------------------------------------------------
        # [Phase 1] Connector (Extract)
        # -----------------------------------------------------------
        packets = []
        try:
            self._log(f"🚀 [Phase 1] Extracting from '{source}'...")
            conn_strat = strategies.get("connector", "auto")

            packets_gen = self.connector.run(source, strategy=conn_strat, **run_config)
            packets = list(packets_gen) if packets_gen else []

            if not packets:
                self._log("⚠️ [Phase 1] No data extracted.", level="warning")
                return stats

            self._log(f"   -> Extracted {len(packets)} packets.")

        except Exception as e:
            self._log(f"💥 [Phase 1] Extraction Failed: {e}", level="error")
            self._emit("on_error", error=e)
            return stats

        # -----------------------------------------------------------
        # [Phase 2] Processing Loop (Transform & Aggregate)
        # -----------------------------------------------------------
        data_buffer = []

        for packet in packets:
            if not packet.success:
                self._log(f"⚠️ Extract error: {packet.error}", level="warning")
                stats["failed"] += 1
                continue

            if not use_refinery:
                data_buffer.append(packet.data)
                stats["read"] += 1
                continue

            items = [packet.data]

            # -------------------------------------------------------
            # [Step 2] Refinery (Optional Transform)
            # -------------------------------------------------------
            if use_refinery:
                try:
                    ref_strat = strategies.get("refinery", "auto")
                    processed_items = self.refinery.run(
                        items, strategy=ref_strat, **run_config
                    )

                    if processed_items:
                        items = processed_items
                    else:
                        continue

                except Exception as e:
                    self._log(f"💥 [Phase 2] Refinery Error: {e}", level="error")
                    stats["failed"] += 1
                    continue

            # 버퍼에 추가
            data_buffer.extend(items)
            stats["read"] += len(items)

        if not data_buffer:
            self._log("⚠️ [Phase 2] No valid data to load.", level="warning")
            return stats

        self._log(f"🚀 [Phase 2] Aggregated {len(data_buffer)} items.")

        # -----------------------------------------------------------
        # [Phase 3] Loader (Load)
        # -----------------------------------------------------------
        try:
            load_strat = strategies.get("loader", "auto")
            self._log(f"🚀 [Phase 3] Loading to '{destination}'...")

            success = self.loader.run(
                input_data=data_buffer,
                destination=destination,
                strategy=load_strat,
                **run_config,
            )

            if success:
                stats["written"] = len(data_buffer)
                self._log(
                    f"✅ [Success] Transfer Complete. Written: {stats['written']}"
                )
            else:
                self._log("❌ [Phase 3] Loader returned failure.", level="error")
                stats["failed"] += len(data_buffer)

        except Exception as e:
            self._log(f"💥 [Phase 3] Load Error: {e}", level="error")
            self._log(traceback.format_exc(), level="error")
            stats["failed"] += len(data_buffer)
            self._emit("on_error", error=e)

        self._emit("on_finish", result_data=stats, success=True)
        return stats
