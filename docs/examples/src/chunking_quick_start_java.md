!!! abstract "Source"
    Synced from [`packages/sayou-chunking/examples/quick_start_java.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-chunking/examples/quick_start_java.py).

## Setup

Split Java source files using `CodeSplitter` with `JavaSplitter`.

**Current status: STUB**

`JavaSplitter` uses regex to detect class and method declarations.  The
class pattern matches access modifiers (`public`, `protected`, `private`,
`static`, `abstract`, `final`) before the `class` keyword.  The method
pattern matches the same modifier combinations followed by a return type,
method name, and opening parenthesis.

**What works today:**

| metadata key    | value                 |
|-----------------|-----------------------|
| `language`      | `"java"`              |
| `semantic_type` | `"code_block"`        |
| `chunk_index`   | position in sequence  |

**What is not yet implemented:**

- `class_name`, `method_name`
- `lineStart` / `lineEnd`
- `calls`, `attribute_calls`, `type_refs`
- Annotation (`@Override`, `@Autowired`) extraction
- Generic type parameter extraction

Full AST support requires `JavaParser` or `tree-sitter-java` integration.

```python
import json

from sayou.chunking.pipeline import ChunkingPipeline
from sayou.chunking.plugins.code_splitter import CodeSplitter

pipeline = ChunkingPipeline(extra_splitters=[CodeSplitter])
print("Pipeline initialized.")

JAVA_SOURCE = """
package com.sayouzone.fabric.connector;

import java.util.List;
import java.util.ArrayList;
import java.util.Optional;

public interface Repository<T, ID> {
    Optional<T> findById(ID id);
    List<T> findAll();
    T save(T entity);
    void deleteById(ID id);
}

public abstract class BaseEntity {
    private String id;
    private long createdAt;

    public BaseEntity(String id) {
        this.id        = id;
        this.createdAt = System.currentTimeMillis();
    }

    public String getId() { return id; }
    public long getCreatedAt() { return createdAt; }
}

public class User extends BaseEntity {
    private String name;
    private String email;

    public User(String id, String name, String email) {
        super(id);
        this.name  = name;
        this.email = email;
    }

    public String getName()  { return name; }
    public String getEmail() { return email; }

    @Override
    public String toString() {
        return String.format("User{id=%s, name=%s}", getId(), name);
    }
}

public class UserRepository implements Repository<User, String> {
    private final List<User> store = new ArrayList<>();

    @Override
    public Optional<User> findById(String id) {
        return store.stream()
                    .filter(u -> u.getId().equals(id))
                    .findFirst();
    }

    @Override
    public List<User> findAll() {
        return new ArrayList<>(store);
    }

    @Override
    public User save(User user) {
        store.removeIf(u -> u.getId().equals(user.getId()));
        store.add(user);
        return user;
    }

    @Override
    public void deleteById(String id) {
        store.removeIf(u -> u.getId().equals(id));
    }

    public Optional<User> findByEmail(String email) {
        return store.stream()
                    .filter(u -> u.getEmail().equals(email))
                    .findFirst();
    }
}
"""
```

## Structural Split

`CodeSplitter` detects `.java` from `extension` and delegates to
`JavaSplitter`.

The regex correctly identifies class declarations and most method
signatures, including those with generics and multiple access modifiers.
Chunks do not cut inside method bodies, but exact boundaries may include
leading whitespace or the start of the following declaration.

```python
chunks = pipeline.run(
    {
        "content": JAVA_SOURCE.strip(),
        "metadata": {"source": "UserRepository.java", "extension": ".java"},
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
        f"lang={m.get('language'):6s}  "
        f"len={len(chunk.content):4d}  "
        f"{first_line[:60]!r}"
    )
```

## Metadata Availability

Until `JavaParser` integration is complete, only the three base fields are
populated.  When full AST support arrives, `class_name`, `method_name`,
`lineStart`, `lineEnd`, and call-graph fields will be added automatically.

```python
print("\n=== Metadata Availability ===")
if chunks:
    sample = chunks[0].metadata
    available = ["language", "semantic_type", "chunk_index"]
    pending = [
        "class_name",
        "method_name",
        "lineStart",
        "lineEnd",
        "calls",
        "attribute_calls",
        "type_refs",
        "annotations",
        "throws",
        "generic_params",
    ]
    for key in available:
        print(f"  [OK]     {key:20s} = {sample.get(key)!r}")
    for key in pending:
        print(f"  [TODO]   {key}")
```

## Save Results

```python
with open("java_chunks.json", "w", encoding="utf-8") as f:
    json.dump([c.model_dump() for c in chunks], f, indent=2, ensure_ascii=False)

print(f"\nSaved {len(chunks)} chunks to java_chunks.json")
```