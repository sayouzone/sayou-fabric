# ── Setup
"""
Split TypeScript source files using `CodeSplitter` with `TypeScriptSplitter`.

**Current status: STUB**

`TypeScriptSplitter` extends the regex approach of `JavaScriptSplitter`
with additional patterns for TypeScript-specific constructs:

- `interface Foo { … }`
- `type Alias = …`
- `abstract class Bar { … }`
- `export async function baz() { … }`

**What works today:**

| metadata key    | value                 |
|-----------------|-----------------------|
| `language`      | `"typescript"`        |
| `semantic_type` | `"code_block"`        |
| `chunk_index`   | position in sequence  |

**What is not yet implemented:**

- `function_name`, `class_name`, `interface_name`, `type_name`
- `lineStart` / `lineEnd`
- `calls`, `attribute_calls`, `type_refs`
- Generic type parameter extraction

`.ts`, `.tsx`, `.mts`, and `.cts` extensions are all supported.
"""
import json

from sayou.chunking.pipeline import ChunkingPipeline
from sayou.chunking.plugins.code_splitter import CodeSplitter

pipeline = ChunkingPipeline(extra_splitters=[CodeSplitter])
print("Pipeline initialized.")

TS_SOURCE = """
import { EventEmitter } from 'events';

export interface UserRecord {
    id:         string;
    name:       string;
    email:      string;
    createdAt:  Date;
}

export type ValidationResult = {
    valid:   boolean;
    errors:  string[];
};

function validateUser(user: Partial<UserRecord>): ValidationResult {
    const errors: string[] = [];
    if (!user.id)    errors.push('id is required');
    if (!user.email) errors.push('email is required');
    return { valid: errors.length === 0, errors };
}

abstract class BaseRepository<T extends { id: string }> {
    protected store: Map<string, T> = new Map();

    abstract findAll(): Promise<T[]>;

    async findById(id: string): Promise<T | undefined> {
        return this.store.get(id);
    }

    async save(entity: T): Promise<void> {
        this.store.set(entity.id, entity);
    }
}

class UserRepository extends BaseRepository<UserRecord> {
    async findAll(): Promise<UserRecord[]> {
        return Array.from(this.store.values());
    }

    async findByEmail(email: string): Promise<UserRecord | undefined> {
        return Array.from(this.store.values()).find(u => u.email === email);
    }
}

export { validateUser, UserRepository };
"""


# ── Structural Split
"""
`CodeSplitter` detects `.ts` from `extension` and delegates to
`TypeScriptSplitter`.  Interface, type alias, abstract class, and function
declarations are used as split boundaries.

Chunks are annotated with `language="typescript"` and
`semantic_type="code_block"`.  The regex splitter correctly identifies
structural boundaries in most real-world TypeScript files.
"""
chunks = pipeline.run(
    {
        "content": TS_SOURCE.strip(),
        "metadata": {"source": "user_repository.ts", "extension": ".ts"},
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
        f"len={len(chunk.content):4d}  "
        f"{chunk.content.strip()[:60]!r}"
    )


# ── TSX (React with TypeScript)
"""
`.tsx` files combine TypeScript syntax with JSX — both interface/type
patterns and JSX component boundaries are detected.
"""
tsx_source = """
import React from 'react';

interface ButtonProps {
    label:    string;
    onClick:  () => void;
    disabled?: boolean;
}

const Button: React.FC<ButtonProps> = ({ label, onClick, disabled = false }) => {
    return (
        <button onClick={onClick} disabled={disabled}>
            {label}
        </button>
    );
};

export default Button;
"""

tsx_chunks = pipeline.run(
    {
        "content": tsx_source.strip(),
        "metadata": {"source": "Button.tsx", "extension": ".tsx"},
        "config": {"chunk_size": 500},
    },
    strategy="code",
)

print("\n=== TSX ===")
for chunk in tsx_chunks:
    print(
        f"  [{chunk.metadata.get('chunk_index', '?')}] {chunk.content.strip()[:60]!r}"
    )


# ── Metadata Availability
"""
Same metadata profile as `JavaScriptSplitter`.  TypeScript-specific fields
(`interface_name`, `type_name`, generic parameters) are on the roadmap.
"""
print("\n=== Metadata Availability ===")
if chunks:
    sample = chunks[0].metadata
    available = ["language", "semantic_type", "chunk_index"]
    pending = [
        "function_name",
        "class_name",
        "interface_name",
        "type_name",
        "lineStart",
        "lineEnd",
        "calls",
        "type_refs",
        "params",
    ]
    for key in available:
        print(f"  [OK]     {key:20s} = {sample.get(key)!r}")
    for key in pending:
        print(f"  [TODO]   {key}")


# ── Save Results
with open("typescript_chunks.json", "w", encoding="utf-8") as f:
    json.dump([c.model_dump() for c in chunks], f, indent=2, ensure_ascii=False)

print(f"\nSaved {len(chunks)} chunks to typescript_chunks.json")
