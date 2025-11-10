import json
import os

from sayou.core.base_component import BaseComponent
from sayou.llm.pipeline import LLMPipeline
from sayou.extractor.pipeline import ExtractorPipeline
from sayou.rag.interfaces.base_fetcher import BaseFetcher
from typing import List, Dict, Any


class SimpleKGContextFetcher(BaseFetcher):
    """
    Assembler가 저장한 KG 파일을 읽어 RAG Context로 변환하는 Fetcher
    """
    component_name = "SimpleKGContextFetcher"
    
    def __init__(self, extractor: ExtractorPipeline):
        self.extractor = extractor
        self.kg_path = None
        self.base_dir = None

    def initialize(self, base_dir: str, **kwargs):
        super().initialize(**kwargs)
        self.base_dir = base_dir
        self.extractor.initialize(base_dir=base_dir, **kwargs)

    def _do_fetch(self, queries: List[str], trace_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """RAGExecutor가 호출하는 실제 로직"""
        if not self.kg_path:
            raise ValueError("kg_path was not set by RAGStage.")
            
        filepath_relative = os.path.basename(self.kg_path)
        raw_json_str = self.extractor.retrieve({"type": "file_read", "filepath": filepath_relative, "base_dir": self.base_dir})
        
        try:
            kg_data = json.loads(raw_json_str)
            refined_contexts = []
            for entity_id, data in kg_data.get("entities", {}).items():
                name = data.get("friendly_name", "").replace("<b>", "").replace("</b>", "")
                t = data.get("attributes", {}).get("sayou:totalTime", "알 수 없음")
                refined_contexts.append(f"- {name} (소요 시간: {t}초)")
            return [{"chunk_content": "\n".join(refined_contexts)}]
        except Exception as e:
            return [{"chunk_content": raw_json_str}] # 실패 시 원본 반환


class RAGExecutionStage(BaseComponent):
    """
    RAG 파이프라인의 최종 단계 (Extractor + LLM).
    'sayou-rag'가 'sayou-extractor'와 'sayou-llm'을 도구로 사용합니다.
    """
    component_name = "RAGExecutionStage"

    def __init__(self, 
        extractor_pipeline: ExtractorPipeline,
        llm_pipeline: LLMPipeline
    ):
        super().__init__()
        self.extractor = extractor_pipeline
        self.llm = llm_pipeline
        self.context_fetcher = SimpleKGContextFetcher(self.extractor)

    def initialize(self, **kwargs):
        """도구들(Extractor, LLM)을 초기화합니다."""
        super().initialize(**kwargs)
        self.context_fetcher.initialize(**kwargs) 
        self.llm.initialize(**kwargs)

    def run(self, query: str, kg_path: str, **kwargs) -> dict:
        """
        [계약] query와 kg_path를 받아 RAG를 수행합니다.
        
        1. Context Fetcher (Extractor 사용)
        2. LLM Pipeline (LLM 사용)
        """
        self._log(f"Running RAG Stage with query: {query}")

        # 1. Extractor로 KG에서 Context 추출
        self.context_fetcher.kg_path = kg_path # 👈 동적으로 KG 경로 주입
        # _do_fetch는 RAGExecutor가 호출해야 하지만, 여기서는 직접 호출로 단순화
        context_chunks = self.context_fetcher._do_fetch(queries=[query], trace_result={})
        context_str = context_chunks[0]["chunk_content"]

        # 2. LLM(도구)을 호출하여 답변 생성
        self._log("Generating final answer...")
        llm_result = self.llm.run(query=query, context=context_str) # 👈 context 주입

        return {
            "answer": llm_result["answer"],
            "context": context_str # 사용된 컨텍스트도 반환
        }