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

            if not os.path.exists(destination):
                os.makedirs(destination, exist_ok=True)

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
        packets_gen = None
        try:
            self._log(f"🚀 [Phase 1] Extracting from '{source}'...")
            conn_strat = strategies.get("connector", "auto")

            packets_gen = self.connector.run(source, strategy=conn_strat, **run_config)

            if not packets_gen:
                self._log("⚠️ [Phase 1] No data generator returned.", level="warning")
                return stats

        except Exception as e:
            self._log(f"💥 [Phase 1] Extraction Failed: {e}", level="error")
            self._emit("on_error", error=e)
            return stats

        # -----------------------------------------------------------
        # [Phase 2] Processing Loop (Transform & Aggregate)
        # -----------------------------------------------------------

        for i, packet in enumerate(packets_gen):
            if not packet.success:
                self._log(f"⚠️ Extract error: {packet.error}", level="warning")
                stats["failed"] += 1
                continue

            stats["read"] += 1

            # 1. Data Preparation
            current_data = packet.data

            # 2. Refinery
            if use_refinery:
                try:
                    ref_strat = strategies.get("refinery", "auto")
                    processed = self.refinery.run(
                        current_data, strategy=ref_strat, **run_config
                    )

                    if processed:
                        current_data = processed
                    else:
                        self._log(f"⚠️ Refinery filtered out item {i}.", level="warning")
                        continue

                except Exception as e:
                    self._log(
                        f"💥 [Phase 2] Refinery Error on item {i}: {e}", level="error"
                    )
                    stats["failed"] += 1
                    continue

            # 3. Dynamic Destination Resolution
            final_path = self._resolve_output_path(destination, packet, i)

            # 4. Loader (Load Immediately)
            try:
                load_strat = strategies.get("loader", "auto")

                success = self.loader.run(
                    input_data=current_data,
                    destination=final_path,
                    strategy=load_strat,
                    **run_config,
                )

                if success:
                    stats["written"] += 1
                    self._log(f"✅ Saved: {os.path.basename(final_path)}")
                else:
                    self._log(f"❌ Failed to save: {final_path}", level="error")
                    stats["failed"] += 1

            except Exception as e:
                self._log(f"💥 [Phase 3] Load Error: {e}", level="error")
                stats["failed"] += 1

        self._emit("on_finish", result_data=stats, success=True)
        return stats

    def _resolve_output_path(self, base_dir: str, packet: Any, index: int) -> str:
        """
        Helper: Generates a unique filename with SMART extension detection.
        """
        import re
        import os

        # 1. Extract metadata
        meta = {}
        if hasattr(packet, "task") and packet.task.meta:
            meta.update(packet.task.meta)
        if isinstance(packet.data, dict):
            meta.update(packet.data.get("meta", {}))

        # 2. Determine file name
        candidate = (
            meta.get("filename")
            or meta.get("subject")
            or meta.get("uid")
            or f"file_{index}"
        )
        safe_name = re.sub(r'[\\/*?:"<>|]', "", str(candidate)).strip()
        safe_name = safe_name.replace(" ", "_")
        if not safe_name:
            safe_name = f"untitled_{index}"

        # 3. Smart Extension
        current_ext = os.path.splitext(safe_name)[1].lower()

        if not current_ext:
            data = packet.data

            # Case A: HTML String
            if isinstance(data, str):
                sample = data[:500].lower().strip()
                if "<html" in sample or "<!doctype html" in sample:
                    safe_name += ".html"
                elif sample.startswith("# ") or "**" in sample:
                    safe_name += ".md"
                else:
                    safe_name += ".txt"

            # Case B: Dictionary / List (JSON)
            elif isinstance(data, (dict, list)):
                safe_name += ".json"

            # Case C: Bytes (Binary)
            elif isinstance(data, bytes):
                safe_name += ".bin"

            # Case D: SayouBlock List
            elif isinstance(data, list) and len(data) > 0 and hasattr(data[0], "type"):
                safe_name += ".json"

            else:
                safe_name += ".json"

        return os.path.join(base_dir, safe_name)
