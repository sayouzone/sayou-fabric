# Design Philosophy

`sayou Data Platform` is built on four core design principles.

---

### 1. Explicit over Implicit
Every operation in Sayou Data Platform is explicit. Users directly compose workflow nodes instead of relying on hidden internal logic.

### 2. Composability
Each module (e.g., Connector, Chunking, LLM) can be installed, replaced, or extended independently.

### 3. Minimal Dependencies
Only `sayou-core` is shared. Each module maintains its own isolated dependency graph.

### 4. 3-Tier Architecture
Every library follows a consistent Interface → Default → Plugin hierarchy.