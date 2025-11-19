# Library Guide: sayou-chunking

`sayou-chunking` is the **context-aware splitting library** designed to bridge the gap between raw text and Knowledge Graphs.

While traditional chunkers blindly slice text by character count, `sayou-chunking` adopts a **"Structure-First"** philosophy. It uses the document's inherent hierarchy (headers, lists) and syntax (markdown tables, code blocks) to create logical, atomic nodes.

Within the `sayou-rag` pipeline, this library accepts clean text from `sayou-refinery` and produces structured chunks for `sayou-wrapper` and `sayou-assembler`.

---

## 1. Core Concepts & Architecture

`sayou-chunking` uses a robust 4-Tier architecture to ensure both stability and extensibility.

### Tier 0: The Engine (Core Utilities)
* **`TextSegmenter`**: The low-level engine responsible for the actual slicing. It implements **"Atomic Protection,"** ensuring that critical patterns (tables, code blocks) are never fragmented, even if they exceed the chunk size.

### Tier 1: Interfaces (The Contract)
* **`BaseSplitter`**: Defines the standard input (`Document` object) and output (`List[Chunk]`). It handles boilerplate logic like error handling and metadata packaging.

### Tier 2: Templates (The Defaults)
* **`RecursiveSplitter`**: The standard infantry. Splits text recursively using separators (Paragraph -> Newline -> Sentence -> Word).
* **`StructureSplitter`**: A generic architect. Splits documents based on user-defined Regex patterns (e.g., splitting by "Article 1", "Section 2").
* **`SemanticSplitter`**: The intelligent analyst. Detects topic shifts using cosine similarity (currently includes a dummy encoder for testing).

### Tier 3: Plugins (Specialized)
* **`MarkdownPlugin`**: The star feature. It understands Markdown syntax to:
    1.  **Protect** tables and code blocks.
    2.  **Classify** chunks (`h1`, `table`, `list_item`).
    3.  **Link** content to headers via `parent_id` for Knowledge Graphs.

### Tier 4: Composites (Advanced Strategies)
* **`ParentDocumentSplitter`**: The commander. It doesn't split text itself but coordinates a "Parent Strategy" (e.g., Markdown) and a "Child Strategy" (e.g., Recursive) to implement **Small-to-Big Retrieval**.

---

## 2. Usage Examples

### 2.1. Markdown Splitting (KG Blueprint)

This is the recommended way to process Markdown files for RAG. It identifies headers as parent nodes and lists/tables as child nodes.

```python
from sayou.chunking.pipeline import ChunkingPipeline
from sayou.chunking.plugins.markdown_plugin import MarkdownPlugin

pipeline = ChunkingPipeline(splitters=[MarkdownPlugin()])
pipeline.initialize()

request = {
    "type": "markdown",
    "content": "# Title\n\nSome text...",
    "metadata": {"id": "doc_1"},
    "chunk_size": 1000
}

chunks = pipeline.split(request)
```

### 2.2. Parent Document Strategy (Composite)

Use this when you want to retrieve small chunks but provide large context to the LLM. It combines `StructureSplitter` (for parents) and `RecursiveSplitter` (for children).

```python
from sayou.chunking.composites.parent_document import ParentDocumentSplitter

# Configure the pipeline
pipeline = ChunkingPipeline(splitters=[ParentDocumentSplitter()])

request = {
    "type": "parent_document",
    "content": "...",
    "config": {
        # Strategy Injection
        "parent_strategy": "structure",
        "structure_pattern": r"\[Section \d+\]", 
        
        # Sizes
        "parent_chunk_size": 2000,
        "chunk_size": 400 
    }
}

chunks = pipeline.split(request)
# Output contains chunks with doc_level='parent' and 'child'
```

---

## 3. The `Chunk` Output Schema

Every splitter returns a list of `Chunk` objects (serialized to Dicts). This schema is designed to be directly consumable by `sayou-assembler`.

```json
{
    "chunk_content": "string (The actual text)",
    "metadata": {
    "chunk_id": "string (Unique ID, e.g., 'doc_1_part_5')",
    "part_index": "int (Order in document)",
    
    // --- Semantic Classification (MarkdownPlugin) ---
    "semantic_type": "Literal['text', 'table', 'code_block', 'h1'...'h6', 'list_item']",
    
    // --- Knowledge Graph Linkage ---
    "parent_id": "Optional[string] (ID of the header or parent chunk)",
    "section_title": "Optional[string] (Text of the parent header)",
    "doc_level": "Literal['parent', 'child'] (For ParentDocument strategy)",
    "child_ids": "List[string] (For Parent nodes to find children)"
    }
}
```

---

## 4. Deep Dive: How Protection Works

One of the biggest challenges in RAG is **broken tables**. `sayou-chunking` solves this at the engine level (Tier 0).

1.  **Registration:** Tier 3 plugins (like `MarkdownPlugin`) register `PROTECTED_PATTERNS` (Regex for tables/code).
2.  **Isolation:** `TextSegmenter` extracts these blocks *before* any splitting occurs.
3.  **Atomic Handling:**
    * If a table is 500 chars and `chunk_size` is 200, it is **NOT** split. It remains as a single 500-char chunk.
    * This ensures the LLM receives the full table context.

---

## 5. Extending (Tier 3 Guide)

To support a new format (e.g., HTML), you should inherit from `RecursiveSplitter` and inject your own patterns.

from sayou.chunking.splitter.recursive import RecursiveSplitter
from sayou.chunking.utils.schema import Document, Chunk

```python
class HtmlPlugin(RecursiveSplitter):
    component_name = "HtmlPlugin"
    SUPPORTED_TYPES = ["html"]

    # 1. Define Protection (e.g., <table>...</table>)
    PROTECTED_PATTERNS = [r"(?s)<table.*?</table>", r"(?s)<pre>.*?</pre>"]
    
    # 2. Define Separators (Tags)
    HTML_SEPARATORS = [r"<div.*?>", r"<p>", "\n"]

    def _do_split(self, doc: Document) -> List[Chunk]:
        # Inject configs
        doc.metadata.setdefault("config", {})
        doc.metadata["config"]["separators"] = self.HTML_SEPARATORS
        doc.metadata["config"]["protected_patterns"] = self.PROTECTED_PATTERNS
        
        return super()._do_split(doc)
```