import os
from typing import Any, Dict, List

from sayou.assembler import AssemblerPipeline
from sayou.chunking import ChunkingPipeline
from sayou.connector import ConnectorPipeline
from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time, safe_run
from sayou.core.schemas import SayouBlock, SayouNode, SayouOutput
from sayou.loader import LoaderPipeline
from sayou.wrapper import WrapperPipeline

from ..core.config import SayouConfig


class StructurePipeline(BaseComponent):
    """
    Advanced Structural Assembly Pipeline.

    Purpose: Transform unstructured raw data (Code, Docs) into structured Knowledge Graphs.
    Flow: Connector -> Chunking -> Wrapper -> Assembler -> Loader
    Ideal for: Code Analysis, RAG Knowledge Base Construction, KG Visualization.
    """

    component_name = "StructurePipeline"

    def __init__(
        self,
        extra_generators=None,
        extra_fetchers=None,
        extra_splitters=None,
        extra_adapters=None,
        extra_builders=None,
        extra_writers=None,
        config: Dict[str, Any] = None,
        **kwargs,
    ):
        """
        Initializes the 5-Stage Pipeline.
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
        [Facade] 1-Line Execution for Knowledge Graph Construction.
        """
        instance = cls(**kwargs)
        return instance.ingest(source, destination, strategies, **kwargs)

    @safe_run(default_return=None)
    def initialize(self, config: Dict[str, Any] = None, **kwargs):
        """
        Propagate configurations to all 5 sub-pipelines.
        """
        if config:
            self.config._config.update(config)
        self.config._config.update(kwargs)
        cfg = self.config

        self.connector.initialize(**cfg.connector)
        self.chunking.initialize(**cfg.chunking)
        self.wrapper.initialize(**cfg.wrapper)
        self.assembler.initialize(**cfg.assembler)
        self.loader.initialize(**cfg.loader)

        self._log("StructurePipeline initialized. 5-Stage Configs propagated.")

    @measure_time
    def ingest(
        self,
        source: str,
        destination: str = None,
        strategies: Dict[str, str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Execute the full construction pipeline.
        Unlike TransferPipeline, this aggregates nodes before Assembly.
        """
        self._emit("on_start", input_data={"source": source, "type": "structure"})
        strategies = strategies or {}
        stats = {"extracted": 0, "chunks": 0, "nodes": 0, "edges": 0, "saved": 0}
        run_config = {**self.config._config, **kwargs}

        # -----------------------------------------------------------
        # [Phase 1] Extraction (Connector)
        # -----------------------------------------------------------
        self._log(f"🚀 [1/5] Extracting from '{source}'...")
        try:
            packets_gen = self.connector.run(
                source, strategy=strategies.get("connector", "auto"), **run_config
            )
            if not packets_gen:
                self._log("⚠️ No data extracted.", level="warning")
                return stats
        except Exception as e:
            self._log(f"💥 Extraction Failed: {e}", level="error")
            return stats

        # -----------------------------------------------------------
        # [Phase 2 & 3] Chunking & Wrapping (Stream Processing)
        # -----------------------------------------------------------

        all_sayou_nodes: List[SayouNode] = []

        self._log(f"⚙️ [2/5 & 3/5] Processing (Chunking -> Wrapping)...")

        for i, packet in enumerate(packets_gen):
            if not packet.success:
                continue

            stats["extracted"] += 1

            raw_data = packet.data
            input_doc = None

            if isinstance(raw_data, dict):
                content = raw_data.get("content", "")
                meta = raw_data.get("meta", {}).copy()

                bad_sources = [None, "", "github_code", "unknown"]

                if meta.get("source") in bad_sources:
                    real_path = (
                        meta.get("file_path") or meta.get("path") or meta.get("title")
                    )

                    if real_path:
                        meta["source"] = real_path
                    else:
                        meta["source"] = f"fallback_file_{i}"

                if "extension" not in meta or not meta["extension"]:
                    file_source = meta.get("source", "")
                    if file_source:
                        _, ext = os.path.splitext(file_source)
                        if ext:
                            meta["extension"] = ext.lower()
                            self._log(f"   [Fix] Injected extension: {ext}")

                if isinstance(content, bytes):
                    try:
                        content = content.decode("utf-8")
                    except:
                        content = str(content)

                input_doc = SayouBlock(content=content, metadata=meta, type="code")

            elif hasattr(raw_data, "content"):
                input_doc = raw_data
                if "source" not in input_doc.metadata:
                    input_doc.metadata["source"] = f"unknown_block_{i}"

            # --- Phase 2: Chunking ---
            chunks = self.chunking.run(
                input_doc, strategy=strategies.get("chunking", "auto"), **run_config
            )

            if not chunks:
                continue

            stats["chunks"] += len(chunks)

            # --- Phase 3: Wrapping ---
            wrapper_output = self.wrapper.run(
                chunks, strategy=strategies.get("wrapper", "auto"), **run_config
            )

            if wrapper_output and wrapper_output.nodes:
                all_sayou_nodes.extend(wrapper_output.nodes)

        if not all_sayou_nodes:
            self._log(
                "❌ No nodes collected after processing all files. Aborting Assembly.",
                level="error",
            )
            return stats

        stats["nodes"] = len(all_sayou_nodes)
        self._log(f"   -> Collected {stats['nodes']} raw nodes.")

        # -----------------------------------------------------------
        # [Phase 4] Assembly (Global Linking)
        # -----------------------------------------------------------
        # Input: List[SayouNode] -> Output: Graph Structure (Nodes + Edges)
        self._log(f"🧠 [4/5] Assembling Structure (Symbol Linking)...")

        try:
            aggregated_input = SayouOutput(nodes=all_sayou_nodes)

            assembly_result = self.assembler.run(
                aggregated_input,
                strategy=strategies.get("assembler", "auto"),
                **run_config,
            )

            if isinstance(assembly_result, dict):
                final_node_count = len(assembly_result.get("nodes", []))
                final_edge_count = len(assembly_result.get("edges", []))
                stats["nodes"] = final_node_count
                stats["edges"] = final_edge_count
                self._log(
                    f"   -> Assembled {final_node_count} nodes, {final_edge_count} edges."
                )

        except Exception as e:
            self._log(f"💥 Assembly Failed: {e}", level="error")
            return stats

        # -----------------------------------------------------------
        # [Phase 5] Loading (Save)
        # -----------------------------------------------------------
        self._log(f"💾 [5/5] Saving to '{destination}'...")

        try:
            success = self.loader.run(
                input_data=assembly_result,
                destination=destination,
                strategy=strategies.get("loader", "auto"),
                **run_config,
            )

            if success:
                stats["saved"] = 1
                self._log("✅ Construction Complete!")
            else:
                self._log("❌ Save Failed.", level="error")

        except Exception as e:
            self._log(f"💥 Loading Failed: {e}", level="error")

        self._emit("on_finish", result_data=stats, success=True)
        return stats
