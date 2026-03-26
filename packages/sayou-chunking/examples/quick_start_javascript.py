# ── Setup
"""
Split JavaScript source files using `CodeSplitter` with `JavaScriptSplitter`.

**Current status: STUB**

`JavaScriptSplitter` uses regex-based structural splitting — not an AST
parser.  It detects top-level `class`, `function`, `const … = function`,
`const … = () =>`, and `export … function` boundaries and splits there
first, then falls back through paragraph and line breaks for oversized
sections.

**What works today:**

| metadata key    | value                 |
|-----------------|-----------------------|
| `language`      | `"javascript"`        |
| `semantic_type` | `"code_block"`        |
| `chunk_index`   | position in sequence  |

**What is not yet implemented:**

- `function_name` — requires JS AST (e.g. via `tree-sitter`)
- `class_name`    — same
- `lineStart` / `lineEnd`
- `calls`, `attribute_calls`, `type_refs` (call-graph)

The splitter still produces meaningful structural boundaries and is useful
for coarse-grained code chunking and embedding.  When JS AST support is
added, the metadata will be upgraded to match `PythonSplitter` output with
no change to the calling code.
"""
import json

from sayou.chunking.pipeline import ChunkingPipeline
from sayou.chunking.plugins.code_splitter import CodeSplitter

pipeline = ChunkingPipeline(extra_splitters=[CodeSplitter])
print("Pipeline initialized.")

JS_SOURCE = """
import { useState, useEffect } from 'react';

const API_URL = 'https://api.example.com';

function fetchData(endpoint) {
    return fetch(`${API_URL}/${endpoint}`)
        .then(res => res.json())
        .catch(err => {
            console.error('Fetch error:', err);
            return null;
        });
}

const processRecord = async (record) => {
    const enriched = { ...record, processed: true };
    return enriched;
};

class DataManager {
    constructor(config) {
        this.config = config;
        this.cache  = new Map();
    }

    async load(key) {
        if (this.cache.has(key)) {
            return this.cache.get(key);
        }
        const data = await fetchData(key);
        this.cache.set(key, data);
        return data;
    }

    clear() {
        this.cache.clear();
    }
}

export default DataManager;
export { fetchData, processRecord };
"""


# ── Structural Split
"""
`CodeSplitter` detects `.js` from `extension` in metadata and delegates
to `JavaScriptSplitter`.

Each chunk carries `language="javascript"` and `semantic_type="code_block"`.
Structural boundaries (class, function, arrow function) are respected so
chunks do not cut mid-definition — but the exact boundaries are approximate
because the splitter uses regex, not a true JS parser.
"""
chunks = pipeline.run(
    {
        "content": JS_SOURCE.strip(),
        "metadata": {"source": "data_manager.js", "extension": ".js"},
        "config": {"chunk_size": 500},
    },
    strategy="code",
)

print("=== Structural Split ===")
for chunk in chunks:
    m = chunk.metadata
    print(
        f"  [{m.get('chunk_index', '?'):2d}]  "
        f"lang={m.get('language'):12s}  "
        f"type={m.get('semantic_type'):12s}  "
        f"len={len(chunk.content):4d}  "
        f"{chunk.content.strip()[:50]!r}"
    )


# ── JSX and Module Variants
"""
`JavaScriptSplitter` also handles `.jsx`, `.mjs`, and `.cjs` files.
Pass the correct extension so `CodeSplitter` can route correctly.
"""
jsx_source = """
import React, { useState } from 'react';

function Counter({ initial = 0 }) {
    const [count, setCount] = useState(initial);
    return (
        <div>
            <button onClick={() => setCount(c => c - 1)}>-</button>
            <span>{count}</span>
            <button onClick={() => setCount(c => c + 1)}>+</button>
        </div>
    );
}

export default Counter;
"""

jsx_chunks = pipeline.run(
    {
        "content": jsx_source.strip(),
        "metadata": {"source": "Counter.jsx", "extension": ".jsx"},
        "config": {"chunk_size": 500},
    },
    strategy="code",
)

print("\n=== JSX ===")
for chunk in jsx_chunks:
    print(
        f"  [{chunk.metadata.get('chunk_index', '?')}] {chunk.content.strip()[:60]!r}"
    )


# ── Metadata Available vs Pending
"""
Print a clear summary of what metadata is populated today and what requires
the future JS AST integration.
"""
print("\n=== Metadata Availability ===")
if chunks:
    sample = chunks[0].metadata
    available = ["language", "semantic_type", "chunk_index"]
    pending = [
        "function_name",
        "class_name",
        "lineStart",
        "lineEnd",
        "calls",
        "attribute_calls",
        "type_refs",
        "params",
        "is_async",
        "is_generator",
        "decorators",
    ]
    for key in available:
        print(f"  [OK]     {key:20s} = {sample.get(key)!r}")
    for key in pending:
        print(f"  [TODO]   {key}")


# ── Save Results
"""
Serialise chunks to JSON.
"""
with open("javascript_chunks.json", "w", encoding="utf-8") as f:
    json.dump([c.model_dump() for c in chunks], f, indent=2, ensure_ascii=False)

print(f"\nSaved {len(chunks)} chunks to javascript_chunks.json")
