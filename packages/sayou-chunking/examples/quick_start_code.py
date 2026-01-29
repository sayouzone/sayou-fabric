import json
import logging

from sayou.chunking.pipeline import ChunkingPipeline
from sayou.chunking.plugins.code_splitter import CodeSplitter

logging.basicConfig(level=logging.INFO, format="%(message)s")


def run_code_demo():
    print(">>> Initializing Sayou Code Chunking Pipeline...")

    pipeline = ChunkingPipeline(extra_splitters=[CodeSplitter])

    # ---------------------------------------------------------
    # [Sample Data] Python Source Code
    # ---------------------------------------------------------
    python_content = """
import os

class DataProcessor:
    def __init__(self, data):
        self.data = data
        self.processed = []
        print("Initialized processor")

    def process(self):
        # This is a processing method
        for item in self.data:
            if item > 0:
                self.processed.append(item * 2)
        return self.processed

    def save(self, path):
        with open(path, "w") as f:
            f.write(str(self.processed))
        print(f"Data saved to {path}")
    """.strip()

    # ---------------------------------------------------------
    # Scenario 1: Python Strategy (Explicit)
    # ---------------------------------------------------------
    print("\n=== [1] Python Code Chunking ===")

    request_py = {
        "content": python_content,
        "metadata": {
            "source": "processor.py",
            "extension": ".py",
        },
        "config": {
            "chunk_size": 1000,
            "chunk_overlap": 0,
        },
    }

    chunks_py = pipeline.run(request_py, strategy="code")

    for i, chunk in enumerate(chunks_py):
        lang = chunk.metadata.get("language", "unknown")
        print(f"[{i}] Lang: {lang} | Len: {len(chunk.content)}")
        print("-" * 40)
        print(chunk.content.strip())
        print("-" * 40)

    # ---------------------------------------------------------
    # Scenario 2: JavaScript Strategy (Inference via Extension)
    # ---------------------------------------------------------
    print("\n=== [2] JavaScript Polyglot Test ===")

    js_content = """
function initMap() {
    const map = new google.maps.Map(document.getElementById("map"), {
        center: { lat: -34.397, lng: 150.644 },
        zoom: 8,
    });
    console.log("Map initialized");
}

class User {
    constructor(name) {
        this.name = name;
    }
    
    sayHello() {
        console.log(`Hello, ${this.name}`);
    }
}
    """.strip()

    request_js = {
        "content": js_content,
        "metadata": {
            "source": "map_component.js",
            "extension": ".js",
        },
        "config": {"chunk_size": 1000},
    }

    chunks_js = pipeline.run(request_js, strategy="code")

    for i, chunk in enumerate(chunks_js):
        print(
            f"[{i}] Lang: {chunk.metadata.get('language')} | Len: {len(chunk.content)}"
        )
        print(f"    Start: {chunk.content.strip()[:40]}...")

    output_data = [c.model_dump() for c in chunks_py + chunks_js]
    with open("examples/code_chunk_result.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print("\n✅ Saved results to examples/code_chunk_result_demo.json")


if __name__ == "__main__":
    run_code_demo()
