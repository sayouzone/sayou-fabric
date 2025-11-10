from typing import List, Optional

from sayou.connector.pipeline import ConnectorPipeline
from sayou.connector.seeder.file_seeder import FileSeeder
from sayou.connector.fetcher.api_fetcher import ApiFetcher

from sayou.wrapper.pipeline import WrapperPipeline
from sayou.wrapper.interfaces.base_mapper import BaseMapper     # 👈 사용자가 제공할 1
from sayou.wrapper.interfaces.base_validator import BaseValidator # 👈 사용자가 제공할 2

from sayou.refinery.pipeline import RefineryPipeline
from sayou.refinery.interfaces.base_processor import BaseProcessor # 👈 사용자가 제공할 3

from sayou.assembler.pipeline import AssemblerPipeline
from sayou.assembler.utils.schema_manager import SchemaManager
from sayou.assembler.utils.schema_validator import SchemaValidator
from sayou.assembler.builder.default_kg_builder import DefaultKGBuilder
from sayou.assembler.storer.file_storer import FileStorer

from .pipeline import SayouRAGPipeline
from .rag_stage import RAGExecutionStage # (이전 제안의 RAG 스테이지)

from sayou.llm.pipeline import LLMPipeline
from sayou.llm.interfaces.base_llm_client import BaseLLMClient # Base client
from sayou.llm.plugins.hf_native_client import HuggingFaceNativeClient # 👈 기본 LLM

from sayou.extractor.pipeline import ExtractorPipeline
from sayou.extractor.retriever.file import FileRetriever

class BasicRAG(SayouRAGPipeline):
    """
    Simplified RAG pipeline for standard use-cases.
    - Focused on minimal, end-to-end flow: data → refine → wrap → assemble → LLM
    """
    def __init__(
            self,
            mapper: BaseMapper,
            validator: BaseValidator,
            refinery_steps: Optional[List[BaseProcessor]] = None,
            llm_client: Optional[BaseLLMClient] = None
        ):
            super().__init__()
            
            self._log("[BasicRAG] Assembling default pipeline...")
            
            # --- 내부 조립 (사용자에게 숨겨짐) ---
            
            # 1. LLM/Extractor (RAG Stage용 도구)
            #   (사용자가 LLM 클라이언트를 주지 않으면, 기본값으로 HF Native 사용)
            _llm_client = llm_client or HuggingFaceNativeClient()
            _llm_pipeline = LLMPipeline(client=_llm_client)
            
            _extractor = ExtractorPipeline(
                retrievers=[FileRetriever()]
            )
            
            # 2. 파이프라인(중간 관리자) 생성
            connector = ConnectorPipeline(
                fetcher=ApiFetcher() # 👈 기본값
            )
            
            wrapper = WrapperPipeline(
                mapper=mapper,       # 👈 사용자가 제공한 *필수* 부품
                validator=validator  # 👈 사용자가 제공한 *필수* 부품
            )
            
            refinery = RefineryPipeline(
                steps=refinery_steps or [] # 👈 (선택적)
            )
            
            assembler = AssemblerPipeline(
                schema_manager=SchemaManager(),
                validator=SchemaValidator(),
                builder=DefaultKGBuilder(), # 👈 기본값
                storer=FileStorer()         # 👈 기본값
            )
            
            rag_stage = RAGExecutionStage(
                extractor_pipeline=_extractor,
                llm_pipeline=_llm_pipeline
            )
            
            # --- 3. 스테이지 등록 ---
            self.add_stage("connector", connector)
            self.add_stage("wrapper", wrapper)
            self.add_stage("refinery", refinery)
            self.add_stage("assembler", assembler)
            self.add_stage("rag_stage", rag_stage)
            
            # 4. 실행 순서 정의 (기존 파이프라인 뼈대와 호환됨)
            self.execution_order = [
                "connector", "wrapper", "refinery", "assembler", "rag_stage"
            ]
            
            self._log("[BasicRAG] Default pipeline assembled successfully.")