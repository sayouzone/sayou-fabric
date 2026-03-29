!!! abstract "Source"
    Synced from [`packages/sayou-loader/examples/quick_start_file.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-loader/examples/quick_start_file.py).

## Setup

Write pipeline output to local files using `LoaderPipeline` with
`FileWriter` and `JsonLineWriter`.

`FileWriter` handles any content type with intelligent extension detection:

| Content type         | Auto-detected extension |
|----------------------|-------------------------|
| ``dict`` / ``list``  | ``.json``               |
| Markdown string      | ``.md``                 |
| HTML string          | ``.html``               |
| CSV string           | ``.csv``                |
| ``bytes`` (PDF magic)| ``.pdf``                |
| ``bytes`` (PNG magic)| ``.png``                |
| plain string         | ``.txt``                |

`JsonLineWriter` writes one JSON object per line — ideal for large
datasets and streaming ingestion.

```python
import json
import os

from sayou.loader.pipeline import LoaderPipeline
from sayou.loader.writer.file_writer import FileWriter
from sayou.loader.writer.jsonl_writer import JsonLineWriter

pipeline = LoaderPipeline(extra_writers=[FileWriter, JsonLineWriter])
```

## Write a Graph to JSON

Pass a dict or list as ``input_data`` with an explicit ``.json``
destination to write structured graph output.

```python
graph = {
    "nodes": [
        {"node_id": "n1", "node_class": "sayou:Topic", "text": "Architecture"},
        {"node_id": "n2", "node_class": "sayou:Text", "text": "Eight libraries."},
        {"node_id": "n3", "node_class": "sayou:Table", "text": "Library | Role"},
    ],
    "edges": [
        {"source": "n2", "target": "n1", "type": "sayou:hasParent"},
        {"source": "n3", "target": "n1", "type": "sayou:hasParent"},
    ],
    "stats": {"node_count": 3, "edge_count": 2},
}

result = pipeline.run(graph, "output/graph.json", strategy="FileWriter")
print("=== Write a Graph to JSON ===")
print(f"  Written : output/graph.json  ({result})")
print(f"  Exists  : {os.path.exists('output/graph.json')}")
```

## Auto-detect Extension

Omit the extension and FileWriter infers it from content.

```python
markdown_text = "# Sayou Fabric\n\nA modular LLM data pipeline library.\n"
result_md = pipeline.run(markdown_text, "output/readme", strategy="FileWriter")
# Auto-detects .md from the leading "# "
md_file = next(
    (p for p in ["output/readme.md", "output/readme.txt"] if os.path.exists(p)), None
)
print("\n=== Auto-detect Extension ===")
print(f"  Written : {md_file}  ({result_md})")
```

## Write Records as JSONL

`JsonLineWriter` streams a list of dicts, one per line — no memory spike
for large datasets.

Trigger automatically via:
- ``strategy="JsonLineWriter"`` (explicit)
- ``.jsonl`` file extension (auto-detected)

```python
records = [
    {"id": "r001", "library": "Connector", "role": "Data collection"},
    {"id": "r002", "library": "Document", "role": "File parsing"},
    {"id": "r003", "library": "Refinery", "role": "Content normalisation"},
    {"id": "r004", "library": "Chunking", "role": "Text splitting"},
    {"id": "r005", "library": "Wrapper", "role": "Schema mapping"},
    {"id": "r006", "library": "Assembler", "role": "Graph / vector assembly"},
    {"id": "r007", "library": "Loader", "role": "Data persistence"},
    {"id": "r008", "library": "Brain", "role": "Orchestration"},
]

result_jl = pipeline.run(records, "output/libraries.jsonl", strategy="auto")
print("\n=== Write Records as JSONL ===")
print(f"  Written : output/libraries.jsonl  ({result_jl})")
with open("output/libraries.jsonl") as f:
    lines = f.readlines()
print(f"  Lines   : {len(lines)}")
print(f"  First   : {json.loads(lines[0])}")
print(f"  Last    : {json.loads(lines[-1])}")
```

## Append Mode

Pass ``mode="a"`` to append to an existing file instead of overwriting.

```python
more_records = [{"id": "r009", "library": "Core", "role": "Shared primitives"}]
pipeline.run(
    more_records, "output/libraries.jsonl", strategy="JsonLineWriter", mode="a"
)

with open("output/libraries.jsonl") as f:
    total_lines = len(f.readlines())

print("\n=== Append Mode ===")
print(f"  Total lines after append: {total_lines}  (was {len(lines)})")
```

## Write Binary Data

Bytes content is written in binary mode.  Extension is auto-detected
from magic bytes if not provided.

```python
fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16  # minimal PNG header
result_img = pipeline.run(fake_png, "output/image", strategy="FileWriter")
img_file = next(
    (p for p in ["output/image.png", "output/image.bin"] if os.path.exists(p)), None
)
print("\n=== Write Binary Data ===")
print(f"  Written : {img_file}  ({result_img})")
```

## Metadata-guided Extension

Wrap content in ``{"content": ..., "metadata": {"extension": ".csv"}}``
to override auto-detection.

```python
csv_text = "name,role,version\nConnector,Collection,0.1\nLoader,Persistence,0.1\n"
envelope = {"content": csv_text, "metadata": {"extension": ".csv"}}
pipeline.run(envelope, "output/libraries", strategy="FileWriter")
print("\n=== Metadata-guided Extension ===")
print(f"  Written : output/libraries.csv  ({os.path.exists('output/libraries.csv')})")
```

## Summary

```python
print("\n=== Written Files ===")
for root, _, files in os.walk("output"):
    for fname in sorted(files):
        path = os.path.join(root, fname)
        size = os.path.getsize(path)
        print(f"  {path}  ({size} bytes)")
```