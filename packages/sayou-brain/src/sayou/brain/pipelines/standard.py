import os
from typing import Any, Dict, List

from sayou.assembler import AssemblerPipeline
from sayou.chunking import ChunkingPipeline
from sayou.connector import ConnectorPipeline
from sayou.core.decorators import measure_time
from sayou.core.schemas import SayouNode, SayouOutput
from sayou.document import DocumentPipeline
from sayou.loader import LoaderPipeline
from sayou.refinery import RefineryPipeline
from sayou.wrapper import WrapperPipeline

from ..core.base_brain import BaseBrainPipeline


class StandardPipeline(BaseBrainPipeline):
    """
    All-in-one document RAG pipeline.

    Orchestrates the full journey from raw data to a searchable knowledge
    store, covering document parsing, content refinement, chunking, semantic
    wrapping, graph/vector assembly, and persistence.

    Flow
    ────
    Connector → Document → Refinery → Chunking → Wrapper → Assembler → Loader

    Use cases
    ─────────
    - Building a RAG knowledge base from PDFs, DOCX, HTML, …
    - Multi-source document ingestion into a vector or graph store
    - End-to-end LLM data pipeline
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
        super().__init__()

        self.config = self._init_config(config, kwargs)
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

        self._sub_pipelines = {
            "connector": self.connector,
            "document": self.document,
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

            StandardPipeline.process(
                "s3://my-bucket/docs/",
                destination="chroma://./chroma_db/sayou_docs",
                extra_splitters=[MyPDFSplitter],
                chunk_size=512,
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
        Execute the full document RAG pipeline.

        Args:
            source: Source URI, directory, or connection string.
            destination: Target store URI / path.  Defaults to a local JSON
                         file named after the source if not supplied.
            strategies: Per-stage strategy overrides (keys: connector, document,
                        refinery, chunking, wrapper, assembler, loader).
        """
        self._emit("on_start", input_data={"source": source, "type": "standard"})
        strategies = strategies or {}
        stats: Dict[str, Any] = {"processed": 0, "failed": 0, "files_count": 0}

        # ── Prep ──────────────────────────────────────────────────────
        if not destination:
            base = os.path.basename(source) if source and "://" not in source else ""
            destination = f"./{os.path.splitext(base)[0] or 'sayou_output'}.json"
            self._log(f"No destination supplied. Defaulting to: {destination}")

        run_config = {**self.config._config, **kwargs}
        self._log(f"StandardPipeline: {source} -> {destination}")

        # ── Phase 1: Extract ─────────────────────────────────────────
        self._log("[1/6] Extracting...")
        try:
            packets = self.connector.run(
                source,
                strategy=strategies.get("connector", "auto"),
                **run_config,
            )
            if packets is None:
                self._log("Connector returned None.", level="warning")
                return stats

            if hasattr(packets, "__len__"):
                if not packets:
                    self._log("Connector returned empty list.", level="warning")
                    return stats
                self._log(f"Fetched {len(packets)} packet(s).")
            else:
                self._log("Connector generator initialised (streaming mode).")

        except Exception as exc:
            self._log(f"[1/6] Extraction failed: {exc}", level="error")
            self._emit("on_error", error=exc)
            return stats

        # ── Phase 2: Per-file processing (Steps 1–4) ─────────────────
        self._log(
            "[2/6] Processing files (Document → Refinery → Chunking → Wrapper)..."
        )
        accumulated_nodes: List[SayouNode] = []

        for packet in packets:
            stats["files_count"] += 1

            if not packet.success:
                self._log(f"Packet failed: {packet.error}", level="warning")
                stats["failed"] += 1
                continue

            file_name = "unknown"
            try:
                file_name = packet.task.meta.get("filename", "unknown_source")
                raw_data = packet.data
            except Exception as exc:
                self._log(f"Meta extraction error: {exc}", level="error")
                self._emit("on_error", error=exc)
                continue

            # Step 1: Document parsing (binary data only)
            doc_obj = None
            if isinstance(raw_data, bytes):
                try:
                    doc_obj = self.document.run(
                        raw_data,
                        file_name,
                        strategy=strategies.get("document", "auto"),
                        **run_config,
                    )
                except Exception as exc:
                    self._log(
                        f"Document parsing failed for {file_name}: {exc}",
                        level="debug",
                    )
                    try:
                        raw_data = raw_data.decode("utf-8")
                    except UnicodeDecodeError:
                        self._log(
                            f"Cannot decode {file_name}. Skipping.", level="error"
                        )
                        stats["failed"] += 1
                        continue

            # Step 2: Refinery
            try:
                refine_input = doc_obj if doc_obj else raw_data
                ref_strat = strategies.get("refinery") or (
                    "standard_doc" if doc_obj else "auto"
                )
                blocks = self.refinery.run(
                    refine_input, strategy=ref_strat, **run_config
                )
                if not blocks:
                    self._log(f"Refinery returned empty blocks for {file_name}.")
                    continue
            except Exception as exc:
                self._log(f"Refinery error on {file_name}: {exc}", level="error")
                stats["failed"] += 1
                self._emit("on_error", error=exc)
                continue

            # Step 3: Chunking
            try:
                all_chunks = self.chunking.run(
                    blocks,
                    strategy=strategies.get("chunking", "auto"),
                    **run_config,
                )
                if not all_chunks:
                    self._log(f"No chunks generated for {file_name}.")
                    continue
            except Exception as exc:
                self._log(f"Chunking error on {file_name}: {exc}", level="error")
                stats["failed"] += 1
                self._emit("on_error", error=exc)
                continue

            # Step 4: Wrapper
            try:
                wrapper_out = self.wrapper.run(
                    all_chunks,
                    strategy=strategies.get("wrapper", "auto"),
                    **run_config,
                )
                if wrapper_out and wrapper_out.nodes:
                    accumulated_nodes.extend(wrapper_out.nodes)
                    stats["processed"] += 1
                    self._log(f"Processed: {file_name}")
            except Exception as exc:
                self._log(f"Wrapper error on {file_name}: {exc}", level="error")
                stats["failed"] += 1
                continue

        # ── Phase 3: Assemble ─────────────────────────────────────────
        if not accumulated_nodes:
            self._log("No nodes collected from any source. Aborting.", level="warning")
            self._emit("on_error", error="No nodes generated.")
            return stats

        self._log(
            f"[5/6] Assembling {len(accumulated_nodes)} nodes from "
            f"{stats['processed']} file(s)..."
        )
        payload = None
        try:
            final_output = SayouOutput(
                nodes=accumulated_nodes,
                metadata={"source_count": stats["processed"], "origin": source},
            )
            payload = self.assembler.run(
                final_output,
                strategy=strategies.get("assembler", "auto"),
                **run_config,
            )
            if not payload:
                self._log("Assembler returned empty payload.", level="warning")
        except Exception as exc:
            self._log(f"[5/6] Assembly failed: {exc}", level="error")
            stats["failed"] += 1
            self._emit("on_error", error=exc)
            return stats

        # ── Phase 4: Load ─────────────────────────────────────────────
        if payload:
            self._log(f"[6/6] Loading to '{destination}'...")
            try:
                success = self.loader.run(
                    payload,
                    destination,
                    strategy=strategies.get("loader", "auto"),
                    **run_config,
                )
                if success:
                    self._log(f"Pipeline complete. Output: {destination}")
                else:
                    self._log("Loader returned False.", level="error")
                    stats["failed"] += 1
            except Exception as exc:
                self._log(f"[6/6] Load failed: {exc}", level="error")
                stats["failed"] += 1
                self._emit("on_error", error=exc)

        self._emit("on_finish", result_data=stats, success=True)
        self._log(f"Stats: {stats}")
        return stats
