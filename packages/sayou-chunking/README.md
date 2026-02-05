# sayou-chunking

[![PyPI version](https://img.shields.io/pypi/v/sayou-chunking.svg?color=blue)](https://pypi.org/project/sayou-chunking/)
[![License](https://img.shields.io/badge/License-Apache%202.0-red.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Docs](https://img.shields.io/badge/docs-mkdocs-success.svg?logo=materialformkdocs)](https://sayouzone.github.io/sayou-fabric/library-guides/chunking/)

**The Structure-Aware Splitter for Sayou Fabric.**

`sayou-chunking` splits large texts into smaller, semantically meaningful units called **Chunks**. Unlike traditional splitters that blindly cut text by character count, this library understands the **syntax structure** of the data.

It focuses on preserving the integrity of code blocks, tables, and JSON objects, ensuring that Retrieval (RAG) systems fetch complete and executable contexts.

---

## 1. Architecture & Role

The Chunking engine takes raw text (from Refinery) and applies a **Syntax-Aware Strategy** to produce atomic chunks.

```mermaid
graph LR
    Text[Refined Text] --> Pipeline[Chunking Pipeline]
    
    subgraph Strategies
        MD[Markdown Header]
        Code[Code AST]
        JSON[JSON Object]
    end
    
    Pipeline -->|Config Routing| Strategies
    Strategies --> Chunks[Atomic Chunks]
```

### 1.1. Core Features
* **Syntax Awareness**: Never splits in the middle of a code block or a markdown table.
* **Hierarchy Preservation**: Attaches metadata about the parent section (e.g., Header Path, Class Name) to every chunk.
* **Atomic Integrity**: Ensures that a JSON object or a Python function remains a single unit.

---

## 2. Available Strategies

`sayou-chunking` prioritizes deterministic structural splitting over probabilistic methods.

| Strategy Key | Target Format | Description |
| :--- | :--- | :--- |
| **`markdown`** | Markdown, Text | Splits by Headers (`#`, `##`). Preserves Tables and Code Blocks as atomic units. |
| **`code`** | Python, JS, Java | Uses AST (Abstract Syntax Tree) to split by Class and Function definitions. |
| **`json`** | JSON, JSONL | Splits large JSON arrays into individual records or sub-trees. |

---

## 3. Installation

```bash
pip install sayou-chunking
```

---

## 4. Usage

The `ChunkingPipeline` is the entry point. It accepts a `ChunkingRequest` containing content and metadata.

### Case A: Markdown Splitting (RAG Standard)

Ideal for documentation. It splits by headers while keeping sections together.

```python
from sayou.chunking import ChunkingPipeline

text_content = """
# Section 1
Introduction text...

## Subsection 1.1
- Item A
- Item B
"""

chunks = ChunkingPipeline.process(
    data={"content": text_content, "metadata": {"source": "doc.md"}},
    strategy="markdown"
)

# 4. Result
for chunk in chunks:
    print(f"[{chunk.metadata['type']}] {chunk.content[:20]}...")
    # Output: [heading] # Section 1...
    # Output: [text] Introduction text...
```

### Case B: Code Splitting (Python AST)

Ideal for code analysis. It splits by logical units (Functions/Classes).

```python
from sayou.chunking import ChunkingPipeline

code_content = """
class MyClass:
    def method_a(self):
        print("hello")

def global_func():
    pass
"""

chunks = ChunkingPipeline.process(
    data={"content": code_content, "metadata": {"language": "python"}},
    strategy="code"
)

# Result: 2 Chunks (1 Class block, 1 Function block)
print(f"Generated {len(chunks)} logic blocks.")
```

### Case C: JSON Splitting

Ideal for processing large data logs or API responses.

```python
from sayou.chunking import ChunkingPipeline

json_content = '[{"id": 1, "val": "A"}, {"id": 2, "val": "B"}]'

chunks = ChunkingPipeline.process(
    data={"content": json_content, "metadata": {}},
    strategy="json"
)

# Result: 2 Chunks (Each object is a separate chunk)
```

---

## 5. Configuration Keys

Customize the behavior of each splitter via the `config` dictionary.

* **`markdown`**: `header_depth` (1-6), `strip_headers` (bool).
* **`code`**: `language` (python), `chunk_lines` (min/max lines).
* **`json`**: `jq_query` (filter pattern), `max_size`.

---

## 6. License

Apache 2.0 License © 2026 **Sayouzone**