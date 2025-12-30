import os
import traceback
from typing import Any, Dict

from sayou.assembler import AssemblerPipeline
from sayou.chunking import ChunkingPipeline
from sayou.connector import ConnectorPipeline
from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time, safe_run
from sayou.core.schemas import SayouOutput
from sayou.document import DocumentPipeline
from sayou.loader import LoaderPipeline
from sayou.refinery import RefineryPipeline
from sayou.wrapper import WrapperPipeline

from ..core.config import SayouConfig


class StandardPipeline(BaseComponent):
    """
    (Tier 1) The All-in-One ETL Orchestrator.

    Automates the entire journey from raw data to database:
    Connector -> Document -> Refinery -> Chunking -> Wrapper -> Assembler -> Loader
    """

    component_name = "StandardPipeline"

    def __init__(
        self,
        extra_generators=None,
        extra_fetchers=None,
        extra_parsers=None,
        extra_normalizers=None,
        extra_processors=None,
        extra_splitters=None,
        extra_adapters=None,
        extra_builders=None,
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

        self.connector = ConnectorPipeline(
            extra_generators=extra_generators,
            extra_fetchers=extra_fetchers,
            **cfg.connector,
        )
        self.document = DocumentPipeline(
            extra_parsers=extra_parsers,
            **cfg.document,
        )
        self.refinery = RefineryPipeline(
            extra_normalizers=extra_normalizers,
            processors=extra_processors,
            **cfg.refinery,
        )
        self.chunking = ChunkingPipeline(
            extra_splitters=extra_splitters,
            **cfg.chunking,
        )
        self.wrapper = WrapperPipeline(
            extra_adapters=extra_adapters,
            **cfg.wrapper,
        )
        self.assembler = AssemblerPipeline(
            extra_builders=extra_builders,
            **cfg.assembler,
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
            StandardPipeline.process(
                "https://...",
                extra_splitters=[MySplitter],
                chunk_size=500
            )
        """
        instance = cls(**kwargs)
        return instance.ingest(source, destination, strategies, **kwargs)

    @safe_run(default_return=None)
    def initialize(self, config: Dict[str, Any] = None, **kwargs):
        """
        [Standard] Initialize all sub-pipelines with new configurations.

        This allows re-configuring the pipeline without recreating it.
        e.g. pipeline.initialize(chunk_size=1000)
        """
        if config:
            self.config._config.update(config)
        self.config._config.update(kwargs)

        cfg = self.config

        self.connector.initialize(**cfg.connector)
        self.document.initialize(**cfg.document)
        self.refinery.initialize(**cfg.refinery)
        self.chunking.initialize(**cfg.chunking)
        self.wrapper.initialize(**cfg.wrapper)
        self.assembler.initialize(**cfg.assembler)
        self.loader.initialize(**cfg.loader)

        self._log("StandardPipeline initialized. Configs propagated.")

    @measure_time
    def ingest(
        self,
        source: str,
        destination: str = None,
        strategies: Dict[str, str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Execute the full ETL pipeline with comprehensive error handling.
        """
        self._emit(
            "on_start", input_data={"source": source, "type": "pipeline_execution"}
        )
        strategies = strategies or {}
        stats = {"processed": 0, "failed": 0, "files_count": 0}

        # -----------------------------------------------------------
        # [Prep] Configuration & Defaults
        # -----------------------------------------------------------
        try:
            # Destination Defaulting
            if not destination:
                base_name = os.path.basename(source) if source else "output"
                if not base_name or "://" in source:
                    base_name = "sayou_output"
                destination = f"./{os.path.splitext(base_name)[0]}.json"
                self._log(f"No destination provided. Defaulting to: {destination}")

            # Runtime Config Merge (Highest Priority)
            run_config = {**self.config._config, **kwargs}
            self._log(f"--- Starting Ingestion: {source} -> {destination} ---")

        except Exception as e:
            self._log(f"💥 [Prep] Configuration Error: {e}", level="error")
            self._log(traceback.format_exc(), level="error")
            self._emit("on_error", error=e)
            return stats

        self._log(
            f"DEBUG: Injecting callbacks to children... (Total: {len(self._callbacks)})"
        )
        if hasattr(self, "_callbacks"):
            for cb in self._callbacks:
                if hasattr(self, "connector"):
                    self.connector.add_callback(cb)
                if hasattr(self, "document"):
                    self.document.add_callback(cb)
                if hasattr(self, "refinery"):
                    self.refinery.add_callback(cb)
                if hasattr(self, "chunking"):
                    self.chunking.add_callback(cb)
                if hasattr(self, "wrapper"):
                    self.wrapper.add_callback(cb)
                if hasattr(self, "assembler"):
                    self.assembler.add_callback(cb)
                if hasattr(self, "loader"):
                    self.loader.add_callback(cb)

        # -----------------------------------------------------------
        # [Phase 1] Connector (Fetch Data)
        # -----------------------------------------------------------
        packets = []
        try:
            self._log(f"🚀 [Phase 1] Connector: Fetching from '{source}'...")

            conn_strat = strategies.get("connector", "auto")
            packets = self.connector.run(source, strategy=conn_strat, **run_config)

            if packets is None:
                self._log("⚠️ [Phase 1] Connector returned None.", level="warning")
                return stats

            if hasattr(packets, "__len__"):
                if not packets:
                    self._log(
                        "⚠️ [Phase 1] Connector returned empty list.", level="warning"
                    )
                    return stats
                self._log(f"   -> Fetched {len(packets)} packets successfully.")

            else:
                self._log(f"   -> Connector generator initialized (Streaming Mode).")

        except Exception as e:
            self._log(f"💥 [Phase 1] Connector Critical Failure", level="error")
            self._log(traceback.format_exc(), level="error")
            self._emit("on_error", error=e)
            return stats

        # -----------------------------------------------------------
        # [Phase 2] Processing Loop (Files -> Nodes)
        # -----------------------------------------------------------
        accumulated_nodes = []

        for packet in packets:
            stats["files_count"] += 1

            # Packet 자체 실패 체크
            if not packet.success:
                self._log(f"⚠️ Fetch failed for packet: {packet.error}", level="warning")
                stats["failed"] += 1
                continue

            # -------------------------------------------------------
            # [Step 0] Meta Extraction
            # -------------------------------------------------------
            file_name = "unknown"
            try:
                file_name = packet.task.meta.get("filename", "unknown_source")
                raw_data = packet.data
                self._log(f"🚀 [Step 0] Processing: {file_name}")
            except Exception as e:
                self._log(f"💥 Error in Step 0 (Meta): {e}", level="error")
                self._emit("on_error", error=e)
                continue

            # -------------------------------------------------------
            # [Step 1] Document Parsing
            # -------------------------------------------------------
            doc_obj = None
            try:
                if isinstance(raw_data, bytes):
                    doc_obj = self.document.run(
                        raw_data,
                        file_name,
                        strategy=strategies.get("document", "auto"),
                        **run_config,
                    )
                    if doc_obj:
                        self._log(f"   -> Document parsed. Type: {type(doc_obj)}")
                        has_type = hasattr(doc_obj, "type")
                        self._log(f"   -> Document has 'type' attr? {has_type}")
                        if has_type:
                            self._log(
                                f"   -> Document.type: {getattr(doc_obj, 'type')}"
                            )

            except Exception as e:
                self._log(
                    f"⚠️ [Step 1] Binary parsing failed for {file_name}. Reason: {e}",
                    level="debug",
                )
                try:
                    raw_data = raw_data.decode("utf-8")
                    self._log("   -> Fallback to text decoding successful.")
                except UnicodeDecodeError:
                    self._log(
                        f"❌ [Step 1] Failed to decode {file_name}. Skipping.",
                        level="error",
                    )
                    stats["failed"] += 1
                    self._emit("on_error", error=e)
                    continue

            # -------------------------------------------------------
            # [Step 2] Refinery
            # -------------------------------------------------------
            try:
                refine_input = doc_obj if doc_obj else raw_data
                ref_strat = strategies.get("refinery")
                if not ref_strat:
                    ref_strat = "standard_doc" if doc_obj else "auto"

                self._log(f"   -> Entering Refinery with strategy: '{ref_strat}'")

                self._log(f"   -> Refinery Input Type: {type(refine_input)}")

                blocks = self.refinery.run(
                    refine_input, strategy=ref_strat, **run_config
                )

                if not blocks:
                    self._log("⚠️ [Step 2] Refinery returned empty blocks.")
                    continue

            except Exception as e:
                self._log(f"💥 [Step 2] Refinery Error on {file_name}", level="error")
                self._log(traceback.format_exc(), level="error")
                stats["failed"] += 1
                self._emit("on_error", error=e)
                continue

            # -------------------------------------------------------
            # [Step 3] Chunking
            # -------------------------------------------------------
            all_chunks = []
            try:
                chunk_strat = strategies.get("chunking", "auto")
                all_chunks = self.chunking.run(
                    blocks, strategy=chunk_strat, **run_config
                )

                if all_chunks:
                    self._log(f"\n[DEBUG] File: {file_name}")
                    self._log(f" - Total Chunks: {len(all_chunks)}")
                    for i, chunk in enumerate(all_chunks[:3]):
                        c_data = (
                            chunk.model_dump()
                            if hasattr(chunk, "model_dump")
                            else chunk
                        )
                        self._log(
                            f" - Chunk[{i}] ID: {c_data.get('metadata', {}).get('chunk_id')}"
                        )
                        self._log(
                            f" - Chunk[{i}] Parent: {c_data.get('metadata', {}).get('parent_id')}"
                        )
                    self._log("--------------------------------------------------\n")
                else:
                    self._log("⚠️ [Step 3] No chunks generated.")
                    continue

            except Exception as e:
                self._log(f"💥 [Step 3] Chunking Error on {file_name}", level="error")
                self._log(traceback.format_exc(), level="error")
                stats["failed"] += 1
                self._emit("on_error", error=e)
                continue

            # -------------------------------------------------------
            # [Step 4] Wrapper & Assembly
            # -------------------------------------------------------
            try:
                wrap_strat = strategies.get("wrapper", "auto")
                wrapper_out = self.wrapper.run(
                    all_chunks, strategy=wrap_strat, **run_config
                )

                if wrapper_out and wrapper_out.nodes:
                    accumulated_nodes.extend(wrapper_out.nodes)
                    stats["processed"] += 1
                    self._log(f"✅ [Finished] Processed {file_name}")

            except Exception as e:
                self._log(f"💥 [Step 4] Wrapper Error on {file_name}", level="error")
                self._log(traceback.format_exc(), level="error")
                stats["failed"] += 1
                continue

        # -----------------------------------------------------------
        # [Phase 3] Finalize: Assemble & Load
        # -----------------------------------------------------------
        if not accumulated_nodes:
            self._log(
                "⚠️ [Phase 3] No nodes generated from any source. Aborting write.",
                level="warning",
            )
            self._emit("on_error", error="No nodes generated from any source.")
            return stats

        self._log(
            f"🚀 [Phase 3] Finalizing... Accumulated {len(accumulated_nodes)} nodes from {stats['processed']} files."
        )

        # -------------------------------------------------------
        # [Step 5] Assembler
        # -------------------------------------------------------
        payload = None
        try:
            final_output = SayouOutput(
                nodes=accumulated_nodes,
                metadata={"source_count": stats["processed"], "origin": source},
            )

            asm_strat = strategies.get("assembler", "auto")
            self._log(f"   -> Assembling payload with strategy: '{asm_strat}'")

            payload = self.assembler.run(final_output, strategy=asm_strat, **run_config)

            if not payload:
                self._log(
                    "⚠️ [Step 5] Assembler returned empty payload.", level="warning"
                )

        except Exception as e:
            self._log(f"💥 [Step 5] Assembler Error", level="error")
            self._log(traceback.format_exc(), level="error")
            stats["failed"] += 1
            self._emit("on_error", error=e)
            return stats

        # -------------------------------------------------------
        # [Step 6] Loader
        # -------------------------------------------------------
        if payload:
            try:
                load_strat = strategies.get("loader", "auto")
                self._log(f"   -> Loading to destination: {destination}")

                success = self.loader.run(
                    payload, destination, strategy=load_strat, **run_config
                )

                if success:
                    self._log(f"✅ [Success] Pipeline Completed. Output: {destination}")
                else:
                    self._log(
                        "❌ [Step 6] Loader reported failure (return False).",
                        level="error",
                    )
                    stats["failed"] += 1

            except Exception as e:
                self._log(f"💥 [Step 6] Loader Critical Error", level="error")
                self._log(traceback.format_exc(), level="error")
                stats["failed"] += 1
                self._emit("on_error", error=e)

        self._emit("on_finish", result_data=stats, success=True)
        self._log(f"--- Ingestion Complete. Stats: {stats} ---")
        return stats
