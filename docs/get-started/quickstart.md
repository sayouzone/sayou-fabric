# Quickstart

Welcome to the Sayou `BasicRAG` Quickstart. This guide will walk you through the core value of Sayou: turning a complex API into an LLM-powered answer in just a few steps.

We will build a pipeline that:
1.  Fetches live data from the Seoul Subway API.
2.  Builds a Knowledge Graph (KG) from the JSON response.
3.  Answers a question using the KG and a local LLM.

The `BasicRAG` facade handles all the complexity, so you only need to focus on **Step 2**.

---

### Step 1: Installation

First, install the `sayou-rag` umbrella package, which includes all necessary components.

```python
pip install sayou-rag
```

---

### Step 2: Define Your Mapping Logic (Your *Only* Job)

`BasicRAG` handles everything *except* one task: it doesn't know how to parse *your specific* API's JSON.

You provide this logic as a simple Python function (`map_logic`). This function receives one item from the API response (`row`) and returns a dictionary for the Knowledge Graph.

You **do not** need to `import BaseMapper` or understand the `sayou-wrapper` library to do this.

```python
import os
import json
from typing import Any, Dict

def seoul_subway_logic(row: Any) -> Dict[str, Any]:
    """
    This is your 'map_logic'.
    It parses one item from the API's 'paths' list.
    """
    if not isinstance(row, dict):
        print(f"Skipping item, expected dict, got {type(row)}")
        return None
    try:
        # We define what the KG will look like.
        return {
            "source": "seoul_api",
            "type": "subway_path",
            "payload": {
                "entity_id": f"sayou:path:{row['dptreStn']['stnNm']}_{row['arvlStn']['stnNm']}",
                "entity_class": "sayou:Path", # Required by the Assembler
                "friendly_name": f"Path: {row['dptreStn']['stnNm']} -> {row['arvlStn']['stnNm']}",
                "attributes": {"sayou:totalTime": row.get("totalreqHr", 120)}
            }
        }
    except KeyError as e:
        print(f"Mapping failed, missing key {e} in item: {row}")
        return None
```

---

### Step 3: Prepare Configuration (The "Boilerplate")

This is the "boring" part—telling Sayou where everything is.

Create a file (`quickstart.py`) and add your `seoul_subway_logic` function from Step 2. Then, add this configuration boilerplate below it.

```python
# --- Configuration Boilerplate ---

# 1. API and Model Paths
# (Get API key from [https://data.seoul.go.kr/](https://data.seoul.go.kr/))
SEOUL_API_KEY = os.environ.get("SEOUL_API_KEY") 
if not SEOUL_API_KEY:
    raise ValueError("SEOUL_API_KEY environment variable is not set.")

API_TARGET_URL = f"[http://openapi.seoul.go.kr:8088/](http://openapi.seoul.go.kr:8088/){SEOUL_API_KEY}/json/getShtrmPath"
API_QUERY = {"url_paths": ["1", "5", "마곡", "강남", "2025-10-31 10:00:00"]}

# (Required: Update this to your local model's path)
LOCAL_MODEL_PATH = "C:/Your/Local/LLM/Model/Path" 
OUTPUT_DIR = "./sayou_quickstart_output"

# 2. Create Output Directory
os.makedirs(OUTPUT_DIR, exist_ok=True)
SCHEMA_PATH = os.path.join(OUTPUT_DIR, "schema.json")
KG_PATH = os.path.join(OUTPUT_DIR, "final_kg.json")

# 3. Create Minimal Schema
# The Assembler needs to know what 'sayou:Path' is.
schema_content = {
    "version": "0.0.1",
    "classes": {"sayou:Path": {"description": "A subway path."}},
    "predicates": {"sayou:totalTime": {}}
}
with open(SCHEMA_PATH, "w", encoding="utf-8") as f:
    json.dump(schema_content, f, indent=2)
```

---

### Step 4: The 3-Line Magic (Create, Init, Run)

Now, add the final three steps to your `quickstart.py` file. This is where the `BasicRAG` facade performs the entire API-to-Answer pipeline.

```python
# 1. Import the Facade
from sayou.rag.pipeline.basic import BasicRAG

print("🚀 Starting Sayou RAG Pipeline (API-to-Answer)...")

# 2. Create: Pass your logic function from Step 2.
#    (BasicRAG auto-loads default components for validation, cleaning, etc.)
pipeline = BasicRAG(
    map_logic=seoul_subway_logic
)

# 3. Initialize: Pass all the configs from Step 3.
pipeline.initialize_all(
    model_path=LOCAL_MODEL_PATH,
    base_dir=OUTPUT_DIR,
    ontology_path=SCHEMA_PATH,
    filepath=KG_PATH,
    target_field="payload.friendly_name" # For the default text cleaner
)

# 4. Run: Provide your query and API info.
final_result = pipeline.run(
    query="Tell me the path from Magok to Gangnam.",
    data_source=(API_TARGET_URL, API_QUERY)
)

# 5. Get the result!
print("\n" + "="*30)
print(f"✅ RAG Answer: {final_result['answer']}")
print(f"✅ Knowledge Graph created at: {KG_PATH}")
```

### Next Steps

You have successfully built an API-to-Answer RAG pipeline.
- To see how `BasicRAG` handles advanced customization (like adding your own text cleaner), continue to the Sayou Agent guide.
- To learn about the "Lego bricks" (`Connector`, `Assembler`, etc.) that `BasicRAG` uses, see the Library Guides.