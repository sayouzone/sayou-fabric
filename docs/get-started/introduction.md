# Introduction

**Sayou Fabric is a framework for Deterministic Knowledge Graph Construction.**

It transforms unstructured data into structured assets by analyzing their intrinsic topology — syntax trees, file hierarchies, and metadata. The result is a Knowledge Graph that is precise, reproducible, and structurally sound.

---

## What Sayou Fabric Does

The full data-to-answer lifecycle is decomposed into discrete, composable stages:

| Stage | Package | Role |
| :--- | :--- | :--- |
| Ingestion | `sayou-connector` | Fetches data from files, APIs, databases, SaaS |
| Parsing | `sayou-document` | Converts documents to structured DOM with layout coordinates |
| Cleaning | `sayou-refinery` | Normalizes, denoises, masks PII |
| Splitting | `sayou-chunking` | Splits by native structure — AST for code, headers for docs |
| Mapping | `sayou-wrapper` | Converts chunks to typed `SayouNode` objects |
| Assembly | `sayou-assembler` | Resolves relationships between nodes into typed edges |
| Persistence | `sayou-loader` | Writes the graph to VectorDB, Graph DB, or file |

The `sayou-brain` orchestrator wires these stages together. You invoke a Pipeline; Brain handles the rest.

---

## Pipeline Modes

**StandardPipeline** — for documents where spatial layout matters (PDF, DOCX, PPTX).
Routes through `sayou-document` to preserve heading hierarchy, table boundaries, and page coordinates before chunking.

**NormalPipeline** — for code, video, and web content.
Skips layout parsing. Routes directly to structural chunking — AST for code, temporal segmentation for video.

---

## Scope

Sayou Fabric is a data layer framework. It produces a clean, queryable Knowledge Graph that any retrieval or generation layer can consume.