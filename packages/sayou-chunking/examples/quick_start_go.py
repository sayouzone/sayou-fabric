# ── Setup
"""
Split Go source files using `CodeSplitter` with `GoSplitter`.

**Current status: STUB**

`GoSplitter` uses regex to detect top-level declarations in Go source
files.  It splits on `func`, `type`, `var`, and `const` declarations at
the package level.

**What works today:**

| metadata key    | value                 |
|-----------------|-----------------------|
| `language`      | `"go"`                |
| `semantic_type` | `"code_block"`        |
| `chunk_index`   | position in sequence  |

**What is not yet implemented:**

- `function_name`, `receiver_type` (for methods)
- `struct_name`, `interface_name`
- `lineStart` / `lineEnd`
- `calls`, `attribute_calls`, `type_refs`
- Import block extraction

Full AST support requires `go/ast` integration via subprocess or
`tree-sitter-go`.

Go's convention of one declaration per top-level block maps naturally to
chunking — the regex approach already aligns with idiomatic Go structure,
making the stub immediately usable for most codebases.
"""
import json

from sayou.chunking.pipeline import ChunkingPipeline
from sayou.chunking.plugins.code_splitter import CodeSplitter

pipeline = ChunkingPipeline(extra_splitters=[CodeSplitter])
print("Pipeline initialized.")

GO_SOURCE = """
package connector

import (
    "context"
    "errors"
    "fmt"
    "sync"
)

const (
    DefaultTimeout = 30
    MaxRetries     = 3
)

var ErrNotFound = errors.New("resource not found")

type Config struct {
    Host     string
    Port     int
    Database string
    Timeout  int
}

type Repository interface {
    FindByID(ctx context.Context, id string) (interface{}, error)
    Save(ctx context.Context, entity interface{}) error
    Delete(ctx context.Context, id string) error
}

type InMemoryRepo struct {
    mu    sync.RWMutex
    store map[string]interface{}
}

func NewInMemoryRepo() *InMemoryRepo {
    return &InMemoryRepo{
        store: make(map[string]interface{}),
    }
}

func (r *InMemoryRepo) FindByID(ctx context.Context, id string) (interface{}, error) {
    r.mu.RLock()
    defer r.mu.RUnlock()

    entity, ok := r.store[id]
    if !ok {
        return nil, fmt.Errorf("%w: id=%s", ErrNotFound, id)
    }
    return entity, nil
}

func (r *InMemoryRepo) Save(ctx context.Context, entity interface{}) error {
    type IDer interface{ GetID() string }
    ider, ok := entity.(IDer)
    if !ok {
        return errors.New("entity must implement GetID() string")
    }

    r.mu.Lock()
    defer r.mu.Unlock()
    r.store[ider.GetID()] = entity
    return nil
}

func (r *InMemoryRepo) Delete(ctx context.Context, id string) error {
    r.mu.Lock()
    defer r.mu.Unlock()
    delete(r.store, id)
    return nil
}

func validateConfig(cfg Config) error {
    if cfg.Host == "" {
        return errors.New("host is required")
    }
    if cfg.Port <= 0 || cfg.Port > 65535 {
        return fmt.Errorf("invalid port: %d", cfg.Port)
    }
    return nil
}
"""


# ── Structural Split
"""
`CodeSplitter` detects `.go` from `extension` and delegates to
`GoSplitter`.

The splitter correctly identifies `func`, `type`, `var`, and `const`
at the package level.  Method receivers (e.g. `func (r *InMemoryRepo)`)
are also caught by the `func` pattern.

Each chunk stays intact — the regex does not cut inside function or
struct bodies — making the output immediately useful for embedding.
"""
chunks = pipeline.run(
    {
        "content": GO_SOURCE.strip(),
        "metadata": {"source": "repository.go", "extension": ".go"},
        "config": {"chunk_size": 600},
    },
    strategy="code",
)

print("=== Structural Split ===")
for chunk in chunks:
    m = chunk.metadata
    first_line = chunk.content.strip().splitlines()[0] if chunk.content.strip() else ""
    print(
        f"  [{m.get('chunk_index', '?'):2d}]  "
        f"lang={m.get('language'):4s}  "
        f"len={len(chunk.content):4d}  "
        f"{first_line[:60]!r}"
    )


# ── Idiomatic Go Alignment
"""
Go's style convention — one top-level declaration per block, clear
separation with blank lines — aligns naturally with the regex splitter.
For most idiomatic Go code, each chunk corresponds to exactly one
exported function, type, or variable declaration.
"""
func_chunks = [c for c in chunks if c.content.strip().startswith("func")]
type_chunks = [c for c in chunks if c.content.strip().startswith("type")]
const_chunks = [c for c in chunks if c.content.strip().startswith("const")]
var_chunks = [c for c in chunks if c.content.strip().startswith("var")]

print("\n=== Declaration Distribution ===")
print(f"  func  : {len(func_chunks)}")
print(f"  type  : {len(type_chunks)}")
print(f"  const : {len(const_chunks)}")
print(f"  var   : {len(var_chunks)}")
print(
    f"  other : {len(chunks) - len(func_chunks) - len(type_chunks) - len(const_chunks) - len(var_chunks)}"
)


# ── Metadata Availability
print("\n=== Metadata Availability ===")
if chunks:
    sample = chunks[0].metadata
    available = ["language", "semantic_type", "chunk_index"]
    pending = [
        "function_name",
        "receiver_type",
        "struct_name",
        "interface_name",
        "lineStart",
        "lineEnd",
        "calls",
        "type_refs",
        "imports",
    ]
    for key in available:
        print(f"  [OK]     {key:20s} = {sample.get(key)!r}")
    for key in pending:
        print(f"  [TODO]   {key}")


# ── Save Results
with open("go_chunks.json", "w", encoding="utf-8") as f:
    json.dump([c.model_dump() for c in chunks], f, indent=2, ensure_ascii=False)

print(f"\nSaved {len(chunks)} chunks to go_chunks.json")
