# Sayou Data Platform

[한국어 (README.ko.md)](./README.ko.md)
> A Modular Open-Source Framework for Building LLM Data Pipelines

[![Build Status](https://img.shields.io/github/actions/workflow/status/sayouzone/sayou-fabric/ci.yml?branch=main)](https://github.com/sayouzone/sayou-fabric/actions)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://github.com/sayouzone/sayou-fabric/LICENSE)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://sayouzone.github.io/sayou-fabric/)

## 1. Core Architecture

`Sayou Data Platform` decomposes the LLM data pipeline by **data flow units** to provide the **stability**, **lightweight footprint**, and **extensibility** required for production environments.

### 1.1. Lightweight & Modular Packages

Every component in the `Sayou Data Platform` is deployed as an **independent Python package**.

* Users install only what they need: `pip install sayou-chunking`.
* Each library minimizes its dependencies (beyond `sayou-core`), preventing conflicts and ensuring lightweight container images.

### 1.2. Consistent 3-Tier Architecture (Interface → Default → Plugin)

All `sayou` libraries follow a consistent 3-Tier design:

* **Tier 1 – Interface:** The standard "socket" for the system (e.g., `BaseFetcher`, `BaseLLMClient`).
* **Tier 2 – Default:** The official, "batteries-included" implementation (e.g., `RecursiveCharacterSplitter`, `OpenAIClient`).
* **Tier 3 – Plugin:** The extension layer where users can plug in their own logic (e.g., an in-house DB connector, a custom LLM) by implementing a T1 interface.

### 1.3. Explicit & Composable Workflow

The `sayou-rag` `RAGExecutor` avoids implicit "magic." It explicitly runs the T1/T2/T3 nodes (Router, Tracer, Fetcher, Generator) that the user assembles. This ensures every step of the RAG pipeline is transparent, controllable, and debuggable.

## 2. Ecosystem Packages

`Sayou Data Platform` includes the following core libraries:

| Package | Status | Description |
| :--- | :--- | :--- |
| `sayou-core` | ![Beta](https://img.shields.io/badge/status-beta-brightgreen) | Core components (BaseComponent, Atom) |
| `sayou-connector` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] Data 'Ingestion' (API, File, DB...) |
| `sayou-wrapper` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] 'Wrap' data into a standard Atom |
| `sayou-chunking` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] Text 'Chunking' strategies |
| `sayou-refinery` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] Data 'Refinement' (Cleaner, Merger...) |
| `sayou-assembler` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] 'Assemble' data (KG Builder...) |
| `sayou-loader` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] 'Load' data (VectorDB, File...) |
| `sayou-extractor` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] 'Extract' data (Retriever, Querier...) |
| `sayou-llm` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] LLM 'Adapter' (OpenAI, Local LLM...) |
| `sayou-rag` | ![Alpha](https://img.shields.io/badge/status-alpha-blue) | [T1/T2/T3] RAG/Agent 'Workflow Executor' |

## 3. Installation

Install only the packages you need.

```bash
# Example 1: Install RAG pipeline with local LLM (Hugging Face)
pip install sayou-rag sayou-llm[transformers] sayou-extractor

# Example 2: Install data collection and chunking modules only
pip install sayou-connector sayou-chunking
```

Refer to the Official Docs for a full list of optional dependencies (extras).

## 4. Quick Start

This Quick Start demonstrates the core value of `sayou-rag`: turning a complex API into a queryable, LLM-powered Knowledge Graph (KG) with minimal setup.

The `BasicRAG` facade handles all complex orchestration (data fetching, JSON parsing, cleaning, KG building, and LLM interfacing) behind the scenes. The user only needs to provide one thing: the data mapping logic.

**1. Installation**
`sayou-rag` is the "umbrella package" that includes `core`, `connector`, `llm`, and all other required libraries.

```bash
pip install sayou-rag
```

**2. The API-to-Answer Example**
This example calls a public API, builds a Knowledge Graph from the response, and uses a local LLM to answer a query about it—all in about 20 lines of user logic.

`quickstart.py`

```python
import os
import json
from typing import Any, Dict

# 1. 🚀 Import the 'BasicRAG' facade.
# You don't need to know about Connectors, Assemblers, or Mappers.
from sayou.rag.pipeline.basic import BasicRAG

# -------------------------------------------------
# 2. 💡 Define your *only* required piece of logic:
# A simple Python function that maps one row of data.
# -------------------------------------------------
def seoul_subway_logic(row: Any) -> Dict[str, Any]:
    """
    Parses one item from the API's 'paths' list.
    No need to inherit from 'BaseMapper' or any class.
    """
    if not isinstance(row, dict):
        print(f"Skipping item, expected dict, got {type(row)}")
        return None
    try:
        return {
            "source": "seoul_api",
            "type": "subway_path",
            "payload": {
                "entity_id": f"sayou:path:{row['dptreStn']['stnNm']}_{row['arvlStn']['stnNm']}",
                "entity_class": "sayou:Path", # The class for the KG
                "friendly_name": f"Path: {row['dptreStn']['stnNm']} -> {row['arvlStn']['stnNm']}",
                "attributes": {"sayou:totalTime": row.get("totalreqHr", 120)}
            }
        }
    except KeyError as e:
        print(f"Mapping failed, missing key {e} in item: {row}")
        return None

# -------------------------------------------------
# 3. 🛠️ Configuration
# -------------------------------------------------
# ❗️ Get your key from: https://data.seoul.go.kr/
SEOUL_API_KEY = os.environ.get("SEOUL_API_KEY")
if not SEOUL_API_KEY:
    raise ValueError("SEOUL_API_KEY environment variable is not set.")

API_TARGET_URL = f"http://openapi.seoul.go.kr:8088/{SEOUL_API_KEY}/json/getShtrmPath"
API_QUERY = {"url_paths": ["1", "5", "마곡", "강남", "2025-10-31 10:00:00"]}

# ❗️ (Required) Update this to your local model's path
LOCAL_MODEL_PATH = "C:/Your/Local/LLM/Model/Path" 
OUTPUT_DIR = "./sayou_quickstart_output"

# Create output dir and a minimal schema for the Assembler
os.makedirs(OUTPUT_DIR, exist_ok=True)
SCHEMA_PATH = os.path.join(OUTPUT_DIR, "schema.json")
KG_PATH = os.path.join(OUTPUT_DIR, "final_kg.json")

schema_content = {
    "version": "0.0.1",
    "classes": {"sayou:Path": {"description": "A subway path."}},
    "predicates": {"sayou:totalTime": {}}
}
with open(SCHEMA_PATH, "w", encoding="utf-8") as f:
    json.dump(schema_content, f, indent=2)

# -------------------------------------------------
# 4. 🪄 Run (Create -> Initialize -> Run)
# -------------------------------------------------
print("🚀 Starting Sayou RAG Pipeline (API-to-Answer)...")

# 1. Create: Pass your custom logic function.
#    (Validator and Cleaner are auto-loaded with defaults)
pipeline = BasicRAG(
    map_logic=seoul_subway_logic
)

# 2. Initialize: Pass all necessary configs.
pipeline.initialize_all(
    model_path=LOCAL_MODEL_PATH,
    base_dir=OUTPUT_DIR,
    ontology_path=SCHEMA_PATH,
    filepath=KG_PATH,
    target_field="payload.friendly_name" # For the default text cleaner
)

# 3. Run: Provide the query and the data source.
final_result = pipeline.run(
    query="Tell me the path from Magok to Gangnam.",
    data_source=(API_TARGET_URL, API_QUERY)
)

print("\n" + "="*30)
print(f"✅ RAG Answer: {final_result['answer']}")
print(f"✅ Knowledge Graph created at: {KG_PATH}")
```

**3. How to Run**
- Get API Key: Get an authentication key from Seoul Open Data Plaza.
- Set Environment Variable:
```bash
# macOS / Linux
export SEOUL_API_KEY="YOUR_API_KEY_HERE"

# Windows (CMD)
set SEOUL_API_KEY="YOUR_API_KEY_HERE"
```
- Update Model Path: Change the `LOCAL_MODEL_PATH` variable to the path of your local GGUF or HuggingFace model.
- Run the script:
```bash
python quickstart.py
```

**4. What Happens?**
The script will execute the full API-to-Answer pipeline. You will see logs from each component as it initializes and runs. Finally, it will create a `final_kg.json` file in the `sayou_quickstart_output` directory and print the LLM's answer to your query.

```
🚀 Starting Sayou RAG Pipeline (API-to-Answer)...
[BaseComponent] [BasicRAG] Assembling default pipeline...
...
[SeoulSubwayMapper] Successfully extracted 22 items.
[SeoulSubwayMapper] Mapping complete. 22 items mapped.
[AssemblerPipeline] Validation complete: 22 / 22 valid atoms.
[FileStorer] Storing KG (22 entities) to ./sayou_quickstart_output/final_kg.json
[RAGExecutionStage] Running RAG Stage with query: Tell me the path from Magok to Gangnam.
...
==============================
✅ RAG Answer: The path from Magok to Gangnam involves transfers at Kkachisan and Sindorim...
✅ Knowledge Graph created at: ./sayou_quickstart_output/final_kg.json
```

## 5. Documentation

Full architecture guides, E2E tutorials, T3 plugin development guides, and API references are available at our **Official Docs Site**.

## 6. Contributing

Contributions are welcome via issues or pull requests. For major changes, please open an issue first to discuss what you would like to change.

**Git Branch Strategy**

- `main`: Production release branch (no direct commits).
- `develop`: Active development branch (all PRs should target this).
- `feature/`, `fix/`: Temporary branches created from develop.

**Workflow**
```Bash
# Sync latest develop branch
git checkout develop
git pull origin develop

# Create a new feature branch
git checkout -b feature/add-semantic-chunker

# Commit and push changes
git commit -m "feat(chunking): Add T2 SemanticChunker"
git push origin feature/add-semantic-chunker
```

## 7. License

Sayou Data Platform(sayou-fabric) is distributed under the Apache License 2.0.