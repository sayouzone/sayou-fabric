import os
from typing import Any, Dict, List, Optional

from sayou.assembler.pipeline import AssemblerPipeline
from sayou.chunking.pipeline import ChunkingPipeline
# Sub-pipelines
from sayou.connector.pipeline import ConnectorPipeline
# Core
from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time, safe_run
from sayou.document.pipeline import DocumentPipeline
from sayou.loader.pipeline import LoaderPipeline
from sayou.refinery.pipeline import RefineryPipeline
from sayou.wrapper.pipeline import WrapperPipeline

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
        # --- Plugin Injection (Pass-through) ---
        extra_generators=None,
        extra_fetchers=None,
        extra_parsers=None,
        extra_normalizers=None,
        extra_processors=None,
        extra_splitters=None,
        extra_adapters=None,
        extra_builders=None,
        extra_writers=None,
        # --- Configuration ---
        config: Dict[str, Any] = None,
        **kwargs,
    ):
        """
        Initializes the Brain. Plugins are passed directly to sub-pipelines.
        """
        super().__init__()

        # 1. Config Setup
        full_config = config or {}
        full_config.update(kwargs)
        self.config = SayouConfig(full_config)
        cfg = self.config

        # 2. Sub-Pipeline Instantiation
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
        Execute the full ETL pipeline.
        """
        strategies = strategies or {}

        # Destination Defaulting
        if not destination:
            base_name = os.path.basename(source) if source else "output"
            if not base_name or "://" in source:
                base_name = "sayou_output"
            destination = f"./{os.path.splitext(base_name)[0]}.json"
            self._log(f"No destination provided. Defaulting to: {destination}")

        stats = {"processed": 0, "failed": 0}

        # Runtime Config Merge (Highest Priority)
        run_config = {**self.config._config, **kwargs}

        self._log(f"--- Starting Ingestion: {source} -> {destination} ---")

        # 1. Connector
        packets = self.connector.run(
            source, strategy=strategies.get("connector", "auto"), **run_config
        )

        for packet in packets:
            if not packet.success:
                self._log(f"Fetch failed: {packet.error}", level="warning")
                stats["failed"] += 1
                continue

            try:
                # Meta
                file_name = packet.task.meta.get("filename", "unknown_source")
                raw_data = packet.data

                # 2. Document
                doc_obj = None
                if isinstance(raw_data, bytes):
                    doc_obj = self.document.run(
                        raw_data,
                        file_name,
                        strategy=strategies.get("document", "auto"),
                        **run_config,
                    )

                refine_input = doc_obj if doc_obj else raw_data

                # 3. Refinery
                ref_strat = strategies.get("refinery")
                if not ref_strat:
                    ref_strat = "standard_doc" if doc_obj else "auto"

                blocks = self.refinery.run(
                    refine_input, strategy=ref_strat, **run_config
                )
                if not blocks:
                    continue

                # 4. Chunking
                chunk_strat = strategies.get("chunking", "auto")
                all_chunks = []
                for block in blocks:
                    chunks = self.chunking.run(
                        block, strategy=chunk_strat, **run_config
                    )
                    all_chunks.extend(chunks)

                if not all_chunks:
                    continue

                # 5. Wrapper
                wrap_strat = strategies.get("wrapper", "auto")
                wrapper_out = self.wrapper.run(
                    all_chunks, strategy=wrap_strat, **run_config
                )

                # 6. Assembler
                asm_strat = strategies.get("assembler", "auto")
                payload = self.assembler.run(
                    wrapper_out, strategy=asm_strat, **run_config
                )

                # 7. Loader
                load_strat = strategies.get("loader", "auto")
                success = self.loader.run(
                    payload, destination, strategy=load_strat, **run_config
                )

                if success:
                    stats["processed"] += 1
                else:
                    stats["failed"] += 1

            except Exception as e:
                self._log(f"Pipeline Error on {file_name}: {e}", level="error")
                stats["failed"] += 1

        self._log(f"--- Ingestion Complete. Stats: {stats} ---")
        return stats
