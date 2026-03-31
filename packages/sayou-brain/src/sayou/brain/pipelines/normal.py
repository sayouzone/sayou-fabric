from typing import Any, Dict, List

from sayou.assembler import AssemblerPipeline
from sayou.chunking import ChunkingPipeline
from sayou.connector import ConnectorPipeline
from sayou.core.decorators import measure_time
from sayou.core.schemas import SayouNode, SayouOutput
from sayou.loader import LoaderPipeline
from sayou.refinery import RefineryPipeline
from sayou.wrapper import WrapperPipeline

from ..core.base_brain import BaseBrainPipeline


class NormalPipeline(BaseBrainPipeline):
    """
    Document knowledge graph pipeline (Refinery-inclusive).

    Extends ``StructurePipeline`` by inserting a Refinery stage between
    the Connector and Chunking to handle raw unstructured text and HTML.

    Flow
    ────
    Connector → Refinery → Chunking → Wrapper → Assembler → Loader

    Use cases
    ─────────
    - Code + document mixed-source knowledge graphs
    - Situations where raw connector output needs normalisation before
      chunking (e.g. HTML stripping, record flattening)
    """

    component_name = "NormalPipeline"

    def __init__(
        self,
        extra_generators=None,
        extra_fetchers=None,
        extra_normalizers=None,
        extra_processors=None,
        extra_splitters=None,
        extra_adapters=None,
        extra_builders=None,
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
        self.chunking = ChunkingPipeline(
            extra_splitters=extra_splitters,
            extra_processors=extra_processors,
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

        self._sub_pipelines = {
            "connector": self.connector,
            "refinery": self.refinery,
            "chunking": self.chunking,
            "wrapper": self.wrapper,
            "assembler": self.assembler,
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

            NormalPipeline.process(
                "./data/",
                destination="bolt://localhost:7687",
            )
        """
        return cls(**kwargs).ingest(source, destination, strategies, **kwargs)

    @measure_time
    def ingest(
        self,
        source: str,
        destination: str = None,
        strategies: Dict[str, str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Execute the Refinery-inclusive knowledge graph pipeline.

        Args:
            source: Source URI or directory path.
            destination: Target store URI / path.
            strategies: Per-stage strategy overrides
                        (keys: connector, refinery, chunking, wrapper,
                        assembler, loader).
        """
        self._emit("on_start", input_data={"source": source, "type": "normal"})
        strategies = strategies or {}
        stats: Dict[str, Any] = {
            "extracted": 0,
            "chunks": 0,
            "nodes": 0,
            "edges": 0,
            "saved": 0,
        }
        run_config = {**self.config._config, **kwargs}

        # ── Phase 1: Extract ─────────────────────────────────────────
        self._log(f"[1/5] Extracting from '{source}'...")
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
            self._log(f"[1/5] Extraction failed: {exc}", level="error")
            self._emit("on_error", error=exc)
            return stats

        # ── Phase 2: Refinery + Chunking + Wrapper (streaming) ───────
        self._log("[2/5] Refinery → Chunking → Wrapper...")
        all_nodes: List[SayouNode] = []

        for packet in packets_gen:
            if not packet.success:
                continue

            stats["extracted"] += 1
            raw_data = packet.data

            # Refinery
            input_doc = self.refinery.run(
                raw_data,
                strategy=strategies.get("refinery", "auto"),
                **run_config,
            )

            # Chunking
            chunks = self.chunking.run(
                input_doc,
                strategy=strategies.get("chunking", "auto"),
                **run_config,
            )
            if not chunks:
                continue

            stats["chunks"] += len(chunks)

            # Wrapper
            wrapper_out = self.wrapper.run(
                chunks,
                strategy=strategies.get("wrapper", "auto"),
                **run_config,
            )
            if wrapper_out and wrapper_out.nodes:
                all_nodes.extend(wrapper_out.nodes)

        if not all_nodes:
            self._log("No nodes collected. Aborting assembly.", level="error")
            return stats

        stats["nodes"] = len(all_nodes)
        self._log(f"Collected {stats['nodes']} nodes.")

        # ── Phase 3: Assemble ─────────────────────────────────────────
        self._log("[3/5] Assembling knowledge graph...")
        try:
            assembly_result = self.assembler.run(
                SayouOutput(nodes=all_nodes),
                strategy=strategies.get("assembler", "auto"),
                **run_config,
            )
            if isinstance(assembly_result, dict):
                stats["nodes"] = len(assembly_result.get("nodes", []))
                stats["edges"] = len(assembly_result.get("edges", []))
                self._log(f"Assembled {stats['nodes']} nodes, {stats['edges']} edges.")
        except Exception as exc:
            self._log(f"[3/5] Assembly failed: {exc}", level="error")
            self._emit("on_error", error=exc)
            return stats

        # ── Phase 4: Load ─────────────────────────────────────────────
        self._log(f"[4/5] Saving to '{destination}'...")
        try:
            success = self.loader.run(
                input_data=assembly_result,
                destination=destination,
                strategy=strategies.get("loader", "auto"),
                **run_config,
            )
            if success:
                stats["saved"] = 1
                self._log("Normal pipeline complete.")
            else:
                self._log("Loader returned False.", level="error")
        except Exception as exc:
            self._log(f"[4/5] Load failed: {exc}", level="error")
            self._emit("on_error", error=exc)

        self._emit("on_finish", result_data=stats, success=True)
        return stats
