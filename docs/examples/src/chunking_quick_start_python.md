!!! abstract "Source"
    Synced from [`packages/sayou-chunking/examples/quick_start_python.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-chunking/examples/quick_start_python.py).

## Setup

Split Python source files using `CodeSplitter` with AST-based analysis.

`PythonSplitter` uses Python's built-in `ast` module to parse source code
into its structural components.  Every chunk corresponds to a real AST
node — a module-level import block, a top-level function, a class header,
a method, or a nested class — preserving exact line boundaries.

This produces significantly richer metadata than regex-based approaches:

| metadata key       | description                                    |
|--------------------|------------------------------------------------|
| `semantic_type`    | `"function"` / `"method"` / `"class_header"` / `"class_attributes"` / `"code_block"` |
| `function_name`    | function or method name                        |
| `class_name`       | class name (class_header chunks)               |
| `parent_node`      | owning class (method chunks)                   |
| `lineStart`        | 1-based inclusive start line                   |
| `lineEnd`          | 1-based inclusive end line                     |
| `inherits_from`    | base class names (class_header only)           |
| `calls`            | direct symbol calls: `foo()`, `Bar()`          |
| `attribute_calls`  | attribute calls: `obj.method()`                |
| `type_refs`        | names from annotations and `isinstance()` checks |
| `params`           | parameter descriptors with kind and annotation |
| `is_async`         | `True` for `async def`                         |
| `is_generator`     | `True` when body contains `yield`              |
| `decorators`       | decorator names                                |
| `raises`           | exception types in `raise` statements          |
| `catches`          | exception types in `except` clauses            |

If AST parsing fails (e.g. invalid or truncated source), `PythonSplitter`
falls back to a regex-based approach and marks chunks with
`metadata["parse_method"] = "regex_fallback"`.

```python
import json

from sayou.chunking.pipeline import ChunkingPipeline
from sayou.chunking.plugins.code_splitter import CodeSplitter

pipeline = ChunkingPipeline(extra_splitters=[CodeSplitter])
print("Pipeline initialized.")

PYTHON_SOURCE = '''
import os
import asyncio
from typing import List, Optional


class DataProcessor:
    """Processes raw records into cleaned output."""

    DEFAULT_BATCH = 100

    def __init__(self, source: str, batch_size: int = DEFAULT_BATCH):
        self.source = source
        self.batch_size = batch_size
        self._cache: List[dict] = []

    def load(self) -> List[dict]:
        """Read all records from source."""
        if not os.path.exists(self.source):
            raise FileNotFoundError(f"Source not found: {self.source}")
        with open(self.source) as f:
            import json
            return json.load(f)

    def validate(self, records: List[dict]) -> List[dict]:
        """Remove records that fail schema checks."""
        valid = []
        for rec in records:
            if isinstance(rec, dict) and "id" in rec:
                valid.append(rec)
        return valid

    async def save_async(self, records: List[dict], dest: str) -> None:
        """Write records asynchronously."""
        await asyncio.sleep(0)   # yield to event loop
        with open(dest, "w") as f:
            import json
            json.dump(records, f, indent=2)


class EnrichedProcessor(DataProcessor):
    """Adds metadata enrichment on top of DataProcessor."""

    def enrich(self, records: List[dict]) -> List[dict]:
        return [{"enriched": True, **r} for r in records]


def run_pipeline(source: str, dest: str) -> int:
    """Top-level entry point.  Returns the number of records written."""
    proc = DataProcessor(source)
    raw  = proc.load()
    clean = proc.validate(raw)
    asyncio.run(proc.save_async(clean, dest))
    return len(clean)


def _internal_helper(value: Optional[str] = None) -> bool:
    """Private helper — illustrates annotation extraction."""
    return value is not None
'''
```

## Structural Chunking

Pass `strategy="code"` and set `extension=".py"` in metadata so
`CodeSplitter` routes to `PythonSplitter`.

Each top-level definition becomes its own chunk.  Class bodies are further
split: one chunk for the class header (plus docstring), one per method, and
one for non-method class body lines (class attributes).

```python
chunks = pipeline.run(
    {
        "content": PYTHON_SOURCE.strip(),
        "metadata": {"source": "processor.py", "extension": ".py"},
        "config": {"chunk_size": 2000},
    },
    strategy="code",
)

print("=== Structural Chunking ===")
for chunk in chunks:
    m = chunk.metadata
    tag = m.get("semantic_type", "?")
    fn = m.get("function_name", m.get("class_name", ""))
    parent = f" [{m['parent_node']}]" if m.get("parent_node") else ""
    lines = f"L{m.get('lineStart', '?')}–{m.get('lineEnd', '?')}"
    print(f"  {tag:20s}{parent:20s} {lines:10s}  {fn}")
```

## Call-Graph Metadata

For every function and method chunk, `PythonSplitter` extracts three
call-graph fields:

- `calls`           — names called directly: `DataProcessor(source)`, `json.load(f)`
- `attribute_calls` — attribute names in call position: `.exists()`, `.load()`
- `type_refs`       — names from annotations and `isinstance()` checks

These are used by `sayou-assembler` to build a symbol call graph that
links chunks across files.

```python
print("\n=== Call-Graph Metadata ===")
for chunk in chunks:
    m = chunk.metadata
    if m.get("semantic_type") not in ("function", "method"):
        continue
    name = (
        f"{m.get('parent_node', '')}.{m['function_name']}"
        if m.get("parent_node")
        else m["function_name"]
    )
    print(f"  {name}")
    if m.get("calls"):
        print(f"    calls           : {m['calls']}")
    if m.get("attribute_calls"):
        print(f"    attribute_calls : {m['attribute_calls']}")
    if m.get("type_refs"):
        print(f"    type_refs       : {m['type_refs']}")
```

## Parameter Descriptors

`params` is a list of dicts, one per parameter:

```python
{
    "name":            "batch_size",
    "kind":            "POSITIONAL_OR_KEYWORD",
    "type_annotation": "int",
    "has_default":     True,
}
```

`kind` follows Python's `inspect.Parameter` taxonomy:
`POSITIONAL_ONLY`, `POSITIONAL_OR_KEYWORD`, `VAR_POSITIONAL`,
`KEYWORD_ONLY`, `VAR_KEYWORD`.

```python
print("\n=== Parameter Descriptors ===")
for chunk in chunks:
    m = chunk.metadata
    params = m.get("params", [])
    if not params:
        continue
    name = m.get("function_name", "?")
    print(f"  {name}()")
    for p in params:
        ann = p.get("type_annotation") or ""
        default = " = …" if p["has_default"] else ""
        print(f"    {p['name']}: {p['kind']:30s} ann={ann!r:12s}{default}")
```

## Class Hierarchy

`class_header` chunks record inheritance via `inherits_from`.
`method` chunks record their owning class via `parent_node`.
Together these two fields let `sayou-assembler` reconstruct
the full class hierarchy without re-parsing the source.

```python
print("\n=== Class Hierarchy ===")
headers = [c for c in chunks if c.metadata.get("semantic_type") == "class_header"]
for h in headers:
    m = h.metadata
    bases = m.get("inherits_from", [])
    methods = [
        c.metadata["function_name"]
        for c in chunks
        if c.metadata.get("parent_node") == m["class_name"]
        and c.metadata.get("semantic_type") == "method"
    ]
    print(f"  class {m['class_name']}({', '.join(bases) if bases else ''})")
    print(f"    methods: {methods}")
```

## Async and Generator Detection

`is_async=True` marks functions defined with `async def`.
`is_generator=True` marks functions whose body contains `yield`.
Both are detected without executing the code.

```python
print("\n=== Async and Generator Detection ===")
for chunk in chunks:
    m = chunk.metadata
    if m.get("semantic_type") not in ("function", "method"):
        continue
    flags = []
    if m.get("is_async"):
        flags.append("async")
    if m.get("is_generator"):
        flags.append("generator")
    if flags:
        print(f"  {m.get('function_name')}: {', '.join(flags)}")
```

## Syntax Error Fallback

When `ast.parse()` raises `SyntaxError`, `PythonSplitter` falls back to
regex-based splitting and marks chunks with `parse_method="regex_fallback"`.

```python
broken_source = "def incomplete(\n    pass\n"

fallback_chunks = pipeline.run(
    {
        "content": broken_source,
        "metadata": {"source": "broken.py", "extension": ".py"},
        "config": {"chunk_size": 2000},
    },
    strategy="code",
)

print("\n=== Syntax Error Fallback ===")
for chunk in fallback_chunks:
    print(
        f"  parse_method={chunk.metadata.get('parse_method', 'ast')}  "
        f"content={chunk.content[:40]!r}"
    )
```

## Save Results

Serialise all chunks to JSON for inspection.
The `model_dump()` output includes the full metadata tree.

```python
with open("python_chunks.json", "w", encoding="utf-8") as f:
    json.dump([c.model_dump() for c in chunks], f, indent=2, ensure_ascii=False)

print(f"\nSaved {len(chunks)} chunks to python_chunks.json")
```