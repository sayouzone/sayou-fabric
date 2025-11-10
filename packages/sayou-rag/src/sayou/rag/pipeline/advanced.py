from sayou.rag.pipeline.pipeline import SayouRAGPipeline
from sayou.connector.pipeline import ConnectorPipeline
from sayou.chunking.pipeline import ChunkingPipeline
from sayou.refinery.pipeline import RefineryPipeline
from sayou.wrapper.pipeline import WrapperPipeline
from sayou.assembler.pipeline import AssemblerPipeline
from sayou.loader.pipeline import LoaderPipeline
from sayou.extractor.pipeline import ExtractorPipeline
from sayou.document.pipeline import DocumentPipeline
from sayou.llm.pipeline import LLMPipeline

class AdvancedRAG(SayouRAGPipeline):
    """
    Fully-featured RAG pipeline with advanced orchestration logic.
    - Includes chunking, document parsing, and multi-source loading.
    """

    def __init__(self):
        super().__init__()

        # 전체 스테이지 순서 정의
        self.execution_order = [
            "connector",
            "chunking",
            "refinery",
            "wrapper",
            "assembler",
            "loader",
            "extractor",
            "document",
            "llm"
        ]

        # 각 스테이지 등록
        self.add_stage("connector", ConnectorPipeline())
        self.add_stage("chunking", ChunkingPipeline())
        self.add_stage("refinery", RefineryPipeline())
        self.add_stage("wrapper", WrapperPipeline())
        self.add_stage("assembler", AssemblerPipeline())
        self.add_stage("loader", LoaderPipeline())
        self.add_stage("extractor", ExtractorPipeline())
        self.add_stage("document", DocumentPipeline())
        self.add_stage("llm", LLMPipeline())

    def run(self, **kwargs) -> Any:
        """
        Override: allow dynamic branching or conditional execution.
        """
        print("[ADVANCED RAG] 🚀 Starting advanced pipeline run...")
        data = kwargs

        for name in self.execution_order:
            if name == "document" and not kwargs.get("contains_documents", False):
                print("[ADVANCED RAG] ⏭️ Skipping 'document' stage (no docs).")
                continue

            stage = self.stages[name]
            if not hasattr(stage, "run"):
                continue

            print(f"[ADVANCED RAG] ▶️ Running stage: {name}")
            try:
                data = stage.run(**(data if isinstance(data, dict) else {"data": data}))
            except Exception as e:
                print(f"[ADVANCED RAG] ❌ Stage {name} failed: {e}")
                break

        print("[ADVANCED RAG] ✅ Advanced pipeline completed.")
        return data
