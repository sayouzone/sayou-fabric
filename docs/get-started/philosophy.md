# Philosophy

## Structure-First

Sayou Fabric parses the **native structure** of data before processing any content.

| Data Type | Native Structure | How Sayou Uses It |
| :--- | :--- | :--- |
| **Code** | AST — classes, methods, imports, call sites | Constructs a typed call graph with CALLS, INHERITS, OVERRIDES, IMPORTS edges |
| **Documents** | Spatial layout, heading hierarchy, table boundaries | Preserves section nesting, never splits a table or code block across chunks |
| **Media** | Temporal timeline, transcript alignment | Sequences segments chronologically with typed NEXT/PREV edges |

This is the **Structure-First Architecture**. The skeleton is built from the data's own organization before any content is touched.

---

## Deterministic

Given the same input, Sayou always produces the same graph. This matters for three reasons:

- **Reproducibility** — the pipeline is testable and auditable.
- **Debuggability** — when a relationship is wrong, there is a specific rule to fix.
- **Stability** — the graph is consistent across environments and over time.

---

## The 3-Tier Design Pattern

Every module in Sayou Fabric follows the same internal structure, inspired by enterprise software architecture:

- **Tier 1 — Interface**: The immutable contract. Abstract base classes defining method signatures and data types. Never changes once released.
- **Tier 2 — Template**: Official, production-tested implementations covering the common cases.
- **Tier 3 — Plugin**: Vendor-specific or domain-specific extensions. New languages, new databases, new APIs — all registered here without touching existing code.

This applies at two levels simultaneously:

- **Micro-level**: each individual library (`sayou-connector`, `sayou-chunking`, …) follows the 3-Tier pattern internally.
- **Macro-level**: the entire ecosystem forms the same pattern — Core as the interface layer, the Data Libraries as templates, Brain as the orchestrator.

---

## Independent Modularity

The ecosystem is split into 10+ independent packages for practical reasons, not engineering purity:

- A data engineer who only needs chunking should not install an LLM adapter.
- A team using their own vector store should not be forced into Sayou's loader.
- Every package follows the same 3-Tier contract, so mixing and matching always works.