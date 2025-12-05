import json
import os
from typing import Any, Dict

from sayou.assembler.pipeline import AssemblerPipeline
from sayou.chunking.pipeline import ChunkingPipeline
from sayou.connector.pipeline import ConnectorPipeline
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
        extra_generators=None,
        extra_fetchers=None,
        extra_parsers=None,
        extra_normalizers=None,
        extra_processors=None,
        extra_splitters=None,
        extra_adapters=None,
        extra_builders=None,
        extra_writers=None,
    ):
        super().__init__()
        self.connector = ConnectorPipeline(
            extra_generators=extra_generators, extra_fetchers=extra_fetchers
        )
        self.document = DocumentPipeline(extra_parsers=extra_parsers)
        self.refinery = RefineryPipeline(
            extra_normalizers=extra_normalizers, processors=extra_processors
        )
        self.chunking = ChunkingPipeline(extra_splitters=extra_splitters)
        self.wrapper = WrapperPipeline(extra_adapters=extra_adapters)
        self.assembler = AssemblerPipeline(extra_builders=extra_builders)
        self.loader = LoaderPipeline(extra_writers=extra_writers)

    @safe_run(default_return=None)
    def initialize(self, config: Dict[str, Any] = None, **kwargs):
        """
        Initialize sub-pipelines with configurations.
        Args:
            config: Nested dict e.g. {'connector': {...}, 'loader': {...}}
        """
        if config:
            self.config = SayouConfig(config)

        cfg = self.config._config

        self.connector.initialize(**cfg.get("connector", {}))
        self.document.initialize(**cfg.get("document", {}))
        self.refinery.initialize(**cfg.get("refinery", {}))
        self.chunking.initialize(**cfg.get("chunking", {}))
        self.wrapper.initialize(**cfg.get("wrapper", {}))
        self.assembler.initialize(**cfg.get("assembler", {}))
        self.loader.initialize(**cfg.get("loader", {}))

        self._log("StandardPipeline initialized. All systems go.")

    @measure_time
    def ingest(
        self, source: str, destination: str, strategies: Dict[str, str] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Execute the ETL pipeline.

        Args:
            source: Input source (File path, URL).
            destination: Output destination (File path, DB URI).
            strategies: Strategy map (e.g., {'connector': 'web_crawl', 'loader': 'neo4j'}).
        """
        strategies = strategies or {}
        stats = {"processed": 0, "failed": 0}

        self._log(f"--- Starting Ingestion: {source} ---")

        # 1. Connector (Source -> List[SayouPacket])
        con_strat = strategies.get("connector", "file")
        packets = self.connector.run(source, strategy=con_strat, **kwargs)

        for packet in packets:
            if not packet.success:
                self._log(f"Fetch failed: {packet.error}", level="warning")
                stats["failed"] += 1
                continue

            try:
                # 2. Document (Binary -> Document Object)
                # Packet 데이터가 Binary(bytes)라면 파싱, 아니면 통과
                doc_data = packet.data
                file_name = packet.task.meta.get("filename", "unknown")

                ext = os.path.splitext(file_name)[1].lower()
                refine_input = doc_data
                refine_strat = "sayou_doc_json"  # Default assumption

                # 2. Document & Type Detection (Smart Routing)
                is_supported_doc = (
                    ext in self.document.handler_map
                    or ext in self.document.image_converter.SUPPORTED_TYPES
                )

                if isinstance(doc_data, bytes):
                    if is_supported_doc:
                        # Case A: Binary Document (PDF, Image, Office)
                        doc_obj = self.document.run(doc_data, file_name)
                        if not doc_obj:
                            stats["failed"] += 1
                            continue
                        refine_input = doc_obj.model_dump()
                        refine_strat = "sayou_doc_json"
                    else:
                        # Case B: Text File (MD, JSON, PY, TXT)
                        try:
                            decoded_text = doc_data.decode("utf-8")
                        except UnicodeDecodeError:
                            self._log(
                                f"Skipping binary file {file_name} (unknown format)",
                                level="warning",
                            )
                            stats["failed"] += 1
                            continue

                        # JSON/JSONL 감지 및 파싱
                        if ext in [".json", ".jsonl"]:
                            try:
                                refine_input = json.loads(decoded_text)
                                refine_strat = "json"  # RecordNormalizer
                            except:
                                refine_input = decoded_text
                                refine_strat = "html"  # Fallback to text
                        else:
                            # 일반 텍스트/마크다운 -> Document Dict 포장
                            # (DocMarkdownNormalizer가 Dict를 원하므로)
                            refine_input = {
                                "metadata": {"title": file_name},
                                "pages": [
                                    {
                                        "elements": [
                                            {"type": "text", "text": decoded_text}
                                        ]
                                    }
                                ],
                            }
                            refine_strat = "sayou_doc_json"

                elif isinstance(doc_data, (dict, list)):
                    # Case C: Already Structured Data (from API etc.)
                    refine_input = doc_data
                    refine_strat = "json"  # RecordNormalizer

                elif isinstance(doc_data, str):
                    # Case D: Raw String (HTML etc.)
                    refine_input = doc_data
                    refine_strat = "html"  # HtmlTextNormalizer

                # [Safety Check] refine_input이 List면 무조건 'json' 전략 사용
                if isinstance(refine_input, list):
                    refine_strat = "json"

                # 3. Refinery
                # 사용자가 전략을 강제했으면 그걸 쓰고, 아니면 위에서 추론한 전략 사용
                actual_ref_strat = strategies.get("refinery", refine_strat)
                blocks = self.refinery.run(refine_input, source_type=actual_ref_strat)

                if not blocks:
                    self._log(
                        f"Refinery produced no blocks for {file_name}", level="warning"
                    )
                    continue

                # 4. Chunking
                all_chunks = []
                chunk_strat = strategies.get("chunking", "default")
                # 마크다운 파일이면 마크다운 청킹 추천
                if ext in [".md", ".markdown"] and "chunking" not in strategies:
                    chunk_strat = "markdown"

                for block in blocks:
                    chunks = self.chunking.run(block, strategy=chunk_strat)
                    all_chunks.extend(chunks)

                if not all_chunks:
                    continue

                # 5. Wrapper
                wrap_strat = strategies.get("wrapper", "document_chunk")
                wrapper_out = self.wrapper.run(all_chunks, strategy=wrap_strat)

                # 6. Assembler
                asm_strat = strategies.get("assembler", "graph")
                payload = self.assembler.run(wrapper_out, strategy=asm_strat)

                # 7. Loader
                load_strat = strategies.get("loader", "file")
                success = self.loader.run(payload, destination, strategy=load_strat)

                if success:
                    stats["processed"] += 1
                else:
                    stats["failed"] += 1

            except Exception as e:
                self._log(f"Critical Pipeline Error on {file_name}: {e}", level="error")
                stats["failed"] += 1

        self._log(f"--- Ingestion Complete. Stats: {stats} ---")
        return stats
