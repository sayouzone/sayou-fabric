from typing import Dict, Any, Optional

from sayou.core.base_component import BaseComponent

# import os
# import sys

# CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# ROOT_DIR = CURRENT_DIR
# while not os.path.exists(os.path.join(ROOT_DIR, "packages")):
#     parent = os.path.dirname(ROOT_DIR)
#     if parent == ROOT_DIR:
#         raise FileNotFoundError("'packages' folder not found.")
#     ROOT_DIR = parent

# PACKAGES_ROOT = os.path.join(ROOT_DIR, "packages")
# sys.path.insert(0, os.path.join(PACKAGES_ROOT, "sayou-core", "."))
# sys.path.insert(0, os.path.join(PACKAGES_ROOT, "sayou-connector", "."))

from sayou.connector.pipeline import ConnectorPipeline
from sayou.document.pipeline import DocumentPipeline
from sayou.refinery.pipeline import RefineryPipeline
from sayou.chunking.pipeline import ChunkingPipeline
from sayou.wrapper.pipeline import WrapperPipeline
from sayou.assembler.pipeline import AssemblerPipeline
from ..components.simple_loader import SimpleLoader
# from ..components.simple_extractor import SimpleExtractor
# from ..components.simple_llm import SimpleLLM

class StandardPipeline(BaseComponent):
    """
    (Tier 1) Sayou RAG의 표준 파이프라인.
    - ingest(): 문서 -> KG 변환 및 저장 (배치)
    - ask(): 질문 -> 검색 -> 답변 (실시간)
    """
    component_name = "StandardPipeline"

    def __init__(self):
        self.connector = ConnectorPipeline()
        self.doc_pipe = DocumentPipeline()
        self.ref_pipe = RefineryPipeline()
        self.chunk_pipe = ChunkingPipeline()
        self.wrap_pipe = WrapperPipeline()
        self.asm_pipe = AssemblerPipeline()
        self.loader = SimpleLoader()
        # self.loader = LoaderPipeline()
        # self.extractor = SimpleExtractor()
        # self.llm = SimpleLLM()

    def initialize(self, **kwargs):
        """모든 하위 파이프라인 초기화"""
        self.connector.initialize(**kwargs)
        self.doc_pipe.initialize(**kwargs)
        self.ref_pipe.initialize(**kwargs)
        self.chunk_pipe.initialize(**kwargs)
        self.wrap_pipe.initialize(**kwargs)
        self.asm_pipe.initialize(**kwargs)
        # self.loader.initialize(**kwargs)
        self._log("All sub-pipelines initialized.")

    # ====================================================
    # Phase 1: Ingestion (Smart Routing ETL)
    # ====================================================
    def ingest(
        self, 
        source: str, 
        strategy: str = "local_scan", 
        save_to: str = "knowledge_graph.json",
        **kwargs
    ) -> Dict[str, Any]:
        
        self._log(f"--- Starting Ingestion: {source} ({strategy}) ---")
        
        total_nodes = 0
        processed_count = 0

        # 1. Connector Loop
        for fetch_result in self.connector.run(source, strategy=strategy, **kwargs):
            source_uri = fetch_result.task.uri 
            
            try:
                if not fetch_result.success:
                    self._log(f"Skipping failed fetch: {source_uri} - {fetch_result.error}")
                    continue

                # 2. 데이터 처리 (라우팅)
                kg_graph = self._process_data(fetch_result)
                
                if kg_graph:
                    # 3. Loader (저장)
                    # (파일 덮어쓰기 방지 로직이 필요하지만 데모용으로 단순화)
                    # self.loader.run(kg_graph, destination=save_to, target_type="file")
                    self.loader.load(kg_graph, destination=save_to)
                    
                    node_count = kg_graph.get("summary", {}).get("node_count", 0)
                    total_nodes += node_count
                    processed_count += 1
                    self._log(f"Processed {source_uri}: {node_count} nodes created.")

            except Exception as e:
                self._log(f"Error processing {source_uri}: {e}")

        self._log(f"Ingestion finished. Processed: {processed_count}, Total Nodes: {total_nodes}")
        return {"status": "success", "processed_items": processed_count, "total_nodes": total_nodes}

    def _process_data(self, result) -> Optional[Dict[str, Any]]:
        """
        단일 FetchResult를 처리하여 KG Graph를 반환하는 내부 라우터.
        """
        data = result.data
        source_uri = result.task.uri
        source_name = os.path.basename(source_uri) if source_uri else "unknown_source"

        # Case A: Binary File (PDF, DOCX...)
        if isinstance(data, bytes):
            self._log(f"Route [Binary]: Parsing document {source_name}")
            
            # Doc -> Refinery -> Markdown String
            doc_obj = self.doc_pipe.run(data, source_name)
            doc_json = doc_obj.model_dump()
            blocks = self.ref_pipe.run(doc_json)
            
            # (Bridge Logic) 리스트를 텍스트로 병합
            # TODO: 이 로직은 추후 sayou-refinery 내부의 'Aggregator' 등으로 고도화 가능
            md_content = "\n\n".join([b.content for b in blocks if b.type == "md"])
            
            return self._process_text(md_content, source_name)

        # Case B: Structured Text/Dict (Web Crawl)
        elif isinstance(data, dict):
            self._log(f"Route [Structured Dict]: Converting to Markdown {source_name}")
            
            # (Bridge Logic) 딕셔너리를 텍스트로 변환
            # TODO: 이 로직도 별도의 Transformer가 담당해야 할 수 있음
            title = data.get("title", "No Title")
            content = data.get("content", "")
            # 링크 정보 제거하고 본문만 사용
            md_content = f"# {title}\n\n{content}"
            
            return self._process_text(md_content, source_name)

        # Case C: List (DB Records) -> Wrapper 직행 (미구현)
        elif isinstance(data, list):
            self._log(f"Route [DB Records]: Skipping (Adapter needed)", level="warning")
            return None

        else:
            self._log(f"Unknown data type: {type(data)}", level="warning")
            return None

    def _process_text(self, text_content: str, source_name: str) -> Dict[str, Any]:
        """
        [Internal Helper] Text -> Chunking -> Wrapper -> Assembler
        현재는 하드코딩되어 있지만, 향후 'TextProcessingPipeline' 등으로 모듈화 가능.
        """
        if not text_content.strip():
            return None

        # 1. Chunking (Markdown Strategy)
        chunk_req = {
            "type": "markdown",
            "content": text_content,
            "metadata": {"source": source_name},
            "chunk_size": 1000
        }
        chunks = self.chunk_pipe.run(chunk_req)

        # 2. Wrapper (Document Chunk Adapter)
        wrapped_data = self.wrap_pipe.run(chunks, adapter_type="document_chunk")

        # 3. Assembler (Hierarchy Strategy)
        kg_graph = self.asm_pipe.run(wrapped_data, strategy="hierarchy")
        
        return kg_graph

    # ====================================================
    # Phase 2: Inference (질문 -> 답변)
    # ====================================================
    def ask(self, query: str, load_from: str = "knowledge_graph.json") -> str:
        self._log(f"--- Starting Inference: {query} ---")

        # 1. Extractor (Storage -> Context)
        context = self.extractor.retrieve(query, source=load_from)

        # 2. LLM (Context + Query -> Answer)
        answer = self.llm.generate(query, context)

        self._log("Inference finished.")
        return answer

    # ====================================================
    # Utility: One-Shot Demo
    # ====================================================
    def run_once(self, file_path: str, query: str):
        """(데모용) 적재 후 즉시 질문"""
        self.ingest(file_path)
        return self.ask(query)