import os
import json
import time
from typing import Dict, Any, List

# ------------------------------------------------------------
# [1] SAYOU CORE IMPORTS
# ------------------------------------------------------------
from sayou.core.atom import DataAtom

from sayou.connector.fetcher.api_fetcher import ApiFetcher

from sayou.refinery.pipeline import Pipeline as RefineryPipeline
from sayou.refinery.processor.text import DefaultTextCleaner

from sayou.assembler.pipeline import Pipeline as AssemblerPipeline
from sayou.assembler.utils.schema_manager import SchemaManager
from sayou.assembler.utils.schema_validator import SchemaValidator
from sayou.assembler.builder.default_kg_builder import DefaultKGBuilder
from sayou.assembler.storer.file_storer import FileStorer

from sayou.extractor.pipeline import Pipeline as ExtractorPipeline
from sayou.extractor.retriever.file import FileRetriever

from sayou.llm.plugins.hf_native_client import HuggingFaceNativeClient

from sayou.rag.interfaces.base_fetcher import BaseFetcher
from sayou.rag.generator.llm_generator import SayouLLMGenerator
from sayou.rag.executor import RAGExecutor


# ------------------------------------------------------------
# [2] SIMPLE RAG ENTRYPOINT
# ------------------------------------------------------------
def simple_rag(
    data_source: dict,
    query: str,
    local_model_path: str,
    api_key: str = None,
    output_dir: str = "./sayou_demo",
    schema_dict: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Run a minimal RAG pipeline (API → KG → LLM Answer)
    ===================================================
    - Fetches API data
    - Wraps into DataAtoms
    - Cleans text
    - Assembles Knowledge Graph
    - Runs RAG (LLM-based answering)

    Args:
        data_source: API URL or JSON path
        query: natural language query
        local_model_path: local LLM path
        api_key: optional, for authenticated APIs
        output_dir: working directory
        schema_dict: optional ontology schema

    Returns:
        {"answer": str, "context": {...}}
    """
    os.makedirs(output_dir, exist_ok=True)
    schema_path = os.path.join(output_dir, "schema.json")
    kg_output_path = os.path.join(output_dir, "final_kg.json")

    print("=== 🚀 [Sayou Simple RAG] Pipeline Started ===")

    # --------------------------------------------------------
    # (1) Connector: API → raw data
    # --------------------------------------------------------
    print("[1/5] 🚚 Fetching data from API...")
    connector = ApiFetcher()
    connector.initialize()
    raw_data = connector.fetch(target=data_source[0], query=data_source[1])
    if not raw_data:
        raise RuntimeError("Connector failed: empty response")

    # --------------------------------------------------------
    # (2) Wrapping: JSON → DataAtoms
    # --------------------------------------------------------
    print("[2/5] 🎁 Wrapping raw JSON into DataAtoms...")
    try:
        print(raw_data)
        parsed = json.loads(raw_data)
        paths = parsed.get("body", {}).get("paths", [])
    except Exception as e:
        raise RuntimeError(f"Invalid JSON structure: {e}")

    atoms = []
    for row in paths:
        atoms.append(DataAtom(
            source="seoul_api",
            type="subway_path",
            payload={
                "entity_id": f"sayou:path:{row['dptreStn']['stnNm']}_{row['arvlStn']['stnNm']}",
                "entity_class": "sayou:Path",
                "friendly_name": f"경로: <b>{row['dptreStn']['stnNm']}</b> → {row['arvlStn']['stnNm']}",
                "attributes": {"sayou:totalTime": 120}
            }
        ))

    print(f"  -> {len(atoms)} atoms created")

    # --------------------------------------------------------
    # (3) Refinery: clean text (remove HTML tags, etc.)
    # --------------------------------------------------------
    print("[3/5] 🧹 Refining text fields...")
    cleaner = DefaultTextCleaner()
    refiner_pipeline = RefineryPipeline(steps=[cleaner])
    refiner_pipeline.initialize(target_field="payload.friendly_name")
    refined_atoms = refiner_pipeline.run(key_atoms=atoms)

    # --------------------------------------------------------
    # (4) Assembler: build KG and store locally
    # --------------------------------------------------------
    print("[4/5] 🏗️ Building and saving KG file...")
    if schema_dict is None:
        schema_dict = {
            "version": "0.0.1",
            "classes": {"sayou:Path": {"description": "지하철 경로"}},
            "predicates": {
                "schema:name": {},
                "sayou:totalTime": {},
                "sayou:hasStartStation": {},
                "sayou:hasEndStation": {}
            }
        }

    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema_dict, f, indent=2)

    assembler_pipeline = AssemblerPipeline(
        schema_manager=SchemaManager(),
        validator=SchemaValidator(),
        builder=DefaultKGBuilder(),
        storer=FileStorer()
    )
    assembler_pipeline.initialize(ontology_path=schema_path, filepath=kg_output_path)
    kg_object = assembler_pipeline.run(atoms=refined_atoms)
    print(f"  -> KG saved at: {kg_output_path}")

    # --------------------------------------------------------
    # (5) RAG: retrieve + generate
    # --------------------------------------------------------
    print("[5/5] 🧠 Running RAG (Local Model)...")

    file_retriever = FileRetriever()
    extractor = ExtractorPipeline(retrievers=[file_retriever])
    extractor.initialize(base_dir=output_dir)

    llm_client = HuggingFaceNativeClient()
    llm_client.initialize(model_path=local_model_path)

    class SimpleFileFetcher(BaseFetcher):
        component_name = "SimpleFileFetcher"
        def __init__(self, extractor):
            self.extractor = extractor
        def _do_fetch(self, queries: List[str], trace_result: Dict[str, Any]) -> List[Dict[str, Any]]:
            filepath_relative = os.path.basename(kg_output_path)
            raw_json_str = self.extractor.retrieve({"type": "file_read", "filepath": filepath_relative, "base_dir": output_dir})
            try:
                kg_data = json.loads(raw_json_str)
                refined_contexts = []
                for entity_id, data in kg_data.get("entities", {}).items():
                    name = data.get("friendly_name", "").replace("<b>", "").replace("</b>", "")
                    t = data.get("attributes", {}).get("sayou:totalTime", "알 수 없음")
                    refined_contexts.append(f"- {name} (소요 시간: {t}초)")
                return [{"chunk_content": "\n".join(refined_contexts)}]
            except Exception as e:
                return [{"chunk_content": raw_json_str}]

    fetcher = SimpleFileFetcher(extractor)
    generator = SayouLLMGenerator(llm_client)
    executor = RAGExecutor(generator=generator, fetcher=fetcher)

    start = time.time()
    result = executor.run(query)
    duration = time.time() - start

    print(f"\n✅ [RAG COMPLETE] ({duration:.2f}s)")
    print(f"💬 Answer: {result['answer']}\n")

    return result
