import os
import json

from typing import Dict, Any, Optional

from sayou.core.base_component import BaseComponent
from sayou.connector.pipeline import ConnectorPipeline
from sayou.document.pipeline import DocumentPipeline
from sayou.refinery.pipeline import RefineryPipeline
from sayou.chunking.pipeline import ChunkingPipeline
from sayou.wrapper.pipeline import WrapperPipeline
from sayou.assembler.pipeline import AssemblerPipeline
from sayou.loader.pipeline import LoaderPipeline

from sayou.extractor.pipeline import ExtractorPipeline
from sayou.llm.pipeline import LLMPipeline

class StandardPipeline(BaseComponent):
    """
    (Tier 1) 데이터 수집부터 지식 적재, 추론까지 담당하는 총괄 파이프라인.
    """
    component_name = "StandardPipeline"

    def __init__(self):
        self.con_pipe = ConnectorPipeline()
        self.doc_pipe = DocumentPipeline()
        self.ref_pipe = RefineryPipeline()
        self.chunk_pipe = ChunkingPipeline()
        self.wrap_pipe = WrapperPipeline()
        self.asm_pipe = AssemblerPipeline()
        self.load_pipe = LoaderPipeline()
        # self.ext_pipe = ExtractorPipeline()
        # self.llm_pipe = LLMPipeline()

    def initialize(self, **kwargs):
        """모든 하위 파이프라인 초기화"""
        self.con_pipe.initialize(**kwargs)
        self.doc_pipe.initialize(**kwargs)
        self.ref_pipe.initialize(**kwargs)
        self.chunk_pipe.initialize(**kwargs)
        self.wrap_pipe.initialize(**kwargs)
        self.asm_pipe.initialize(**kwargs)
        self.load_pipe.initialize(**kwargs)
        self._log("All sub-pipelines initialized.")

    # ====================================================
    # Phase 1: Ingestion (Accumulative Load)
    # ====================================================
    def ingest(
        self, 
        source: str, 
        strategy: str = "local_scan", 
        save_to: str = "knowledge_graph.json",
        loader_type: str = "file", 
        overwrite: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        
        self._log(f"--- Starting Ingestion: {source} -> {save_to} ---")

        master_graph = {"nodes": [], "edges": [], "summary": {"node_count": 0, "edge_count": 0}}
        if not overwrite and loader_type == "file" and os.path.exists(save_to):
            try:
                self._log(f"Loading existing KG from '{save_to}'...")
                with open(save_to, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                    self._merge_graphs(master_graph, existing)
            except Exception as e:
                self._log(f"Failed to load existing KG: {e}")

        processed_count = 0
        new_nodes_count = 0

        for fetch_result in self.con_pipe.run(source, strategy=strategy, **kwargs):
            source_uri = fetch_result.task.uri
            try:
                if not fetch_result.success:
                    continue

                current_graph = self._process_data(fetch_result)                
                if current_graph:
                    self._merge_graphs(master_graph, current_graph)
                    
                    count = current_graph.get("summary", {}).get("node_count", 0)
                    new_nodes_count += count
                    processed_count += 1
                    self._log(f"Merged {os.path.basename(source_uri)}: +{count} nodes")

            except Exception as e:
                self._log(f"Error processing {source_uri}: {e}")

        self._log(f"Saving total {len(master_graph['nodes'])} nodes to {save_to}...")
        
        success = self.load_pipe.run(
            data=master_graph, 
            destination=save_to, 
            target_type=loader_type
        )
        
        return {
            "status": "success" if success else "failed", 
            "processed_files": processed_count,
            "total_nodes": len(master_graph['nodes'])
        }

    def _merge_graphs(self, base_graph: Dict[str, Any], new_graph: Dict[str, Any]):
        """
        (Helper) 두 개의 그래프 딕셔너리를 병합합니다.
        Node ID 충돌 시, 새로운 것으로 덮어쓰거나 유지하는 정책을 적용합니다.
        """
        node_map = {n['id']: n for n in base_graph.get('nodes', [])}
        for node in new_graph.get('nodes', []):
            node_map[node['id']] = node

        base_graph['nodes'] = list(node_map.values())
        base_edges = base_graph.get('edges', [])
        new_edges = new_graph.get('edges', [])
        base_edges.extend(new_edges)
        base_graph['edges'] = base_edges

        base_graph['summary'] = {
            "node_count": len(base_graph['nodes']),
            "edge_count": len(base_graph['edges'])
        }

    def _process_data(self, result) -> Optional[Dict[str, Any]]:
        data = result.data
        source_uri = result.task.uri
        source_name = os.path.basename(source_uri) if source_uri else "unknown_source"

        if isinstance(data, bytes):
            doc_obj = self.doc_pipe.run(data, source_name)
            doc_json = doc_obj.model_dump()
            blocks = self.ref_pipe.run(doc_json)
            md_content = "\n\n".join([b.content for b in blocks if b.type == "md"])
            return self._process_text(md_content, source_name)

        elif isinstance(data, dict):
            title = data.get("title", "No Title")
            content = data.get("content", "")
            md_content = f"# {title}\n\n{content}"
            return self._process_text(md_content, source_name)
            
        return None

    def _process_text(self, text_content: str, source_name: str) -> Dict[str, Any]:
        if not text_content.strip(): return None
        chunk_req = {"type": "markdown", "content": text_content, "metadata": {"source": source_name}, "chunk_size": 1000}
        chunks = self.chunk_pipe.run(chunk_req)
        wrapped_data = self.wrap_pipe.run(chunks, adapter_type="document_chunk")
        kg_graph = self.asm_pipe.run(wrapped_data, strategy="hierarchy")
        return kg_graph

    # ====================================================
    # Phase 2: Inference (질문 -> 답변)
    # ====================================================
    def ask(self, query: str, load_from: str = "knowledge_graph.json") -> str:
        self._log(f"--- Starting Inference: {query} ---")

        context = self.ext_pipe.retrieve(query, source=load_from)

        answer = self.llm_pipe.generate(query, context)

        self._log("Inference finished.")
        return answer

    # ====================================================
    # Utility: One-Shot Demo
    # ====================================================
    def run_once(self, file_path: str, query: str):
        """(데모용) 적재 후 즉시 질문"""
        self.ingest(file_path)
        return self.ask(query)