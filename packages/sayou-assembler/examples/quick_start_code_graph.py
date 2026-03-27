# ── Setup
"""
Build a code knowledge graph from SayouNodes using `AssemblerPipeline`
with `CodeGraphBuilder`.

`CodeGraphBuilder` is the second pass after `CodeChunkAdapter`.  It
receives `SayouNode` objects (File, Class, Method, Function, CodeBlock, …)
and resolves all raw call-graph metadata into typed, confidence-annotated
edges.

Edge types produced
───────────────────
CONTAINS      FILE → CLASS/FUNC/METHOD/BLOCK        (structural)
              CLASS → METHOD/ATTRIBUTE_BLOCK         (structural)
IMPORTS       BLOCK → FILE/SYMBOL                   (resolved import)
CALLS         FUNC/METHOD → FUNC/METHOD              HIGH / DIRECT
MAYBE_CALLS   FUNC/METHOD → FUNC/METHOD              LOW  / HEURISTIC
INHERITS      CLASS → CLASS                         HIGH / DIRECT
OVERRIDES     METHOD → METHOD                       HIGH / INFERRED
USES_TYPE     FUNC/METHOD → CLASS                   MEDIUM / INFERRED
MUTATES_GLOBAL FUNC/METHOD → CODE_BLOCK             HIGH / DIRECT
RAISES        FUNC/METHOD → virtual exc node        HIGH / DIRECT
EXPOSES       FILE → FUNC/CLASS  (__all__)           HIGH / DIRECT

Design
──────
- Phase 1: index all nodes (file_map, symbol_map, class_map, method_map, …)
- Phase 2: generate edges by scanning every node's raw attributes
- Post-pass: OVERRIDES (needs full method index) and EXPOSES (__all__)

The full production flow is:

    ChunkingPipeline  (PythonSplitter)
         ↓  List[SayouChunk]
    WrapperPipeline   (CodeChunkAdapter)
         ↓  SayouOutput  [File, Class, Method, …]
    AssemblerPipeline (CodeGraphBuilder)
         ↓  {"nodes": […], "edges": […]}
    LoaderPipeline    (Neo4jWriter / FileWriter)
"""
import json

from sayou.core.ontology import (
    SayouAttribute,
    SayouClass,
    SayouEdgeMeta,
    SayouPredicate,
)
from sayou.core.schemas import SayouNode, SayouOutput

from sayou.assembler.pipeline import AssemblerPipeline
from sayou.assembler.plugins.code_graph_builder import CodeGraphBuilder

pipeline = AssemblerPipeline(extra_builders=[CodeGraphBuilder])

SRC = "sayou/refinery/pipeline.py"
SRC2 = "sayou/refinery/base_normalizer.py"


# ── Sample Code Nodes
"""
These nodes replicate the output of `WrapperPipeline + CodeChunkAdapter`
applied to a small Python module pair.  In production they arrive
automatically from the chunking → wrapping stage.
"""


def _file(path, **attrs):
    return SayouNode(
        node_id=f"sayou:file:{path.replace('/', '_')}",
        node_class=SayouClass.FILE,
        attributes={SayouAttribute.FILE_PATH: path, **attrs},
    )


def _class(name, path=SRC, **attrs):
    return SayouNode(
        node_id=f"sayou:class:{path.replace('/', '_')}::{name}",
        node_class=SayouClass.CLASS,
        attributes={
            SayouAttribute.FILE_PATH: path,
            SayouAttribute.SYMBOL_NAME: name,
            **attrs,
        },
    )


def _method(name, parent, path=SRC, **attrs):
    return SayouNode(
        node_id=f"sayou:method:{path.replace('/', '_')}::{parent}.{name}",
        node_class=SayouClass.METHOD,
        attributes={
            SayouAttribute.FILE_PATH: path,
            SayouAttribute.SYMBOL_NAME: name,
            SayouAttribute.PARENT_CLASS: parent,
            **attrs,
        },
    )


def _func(name, path=SRC, **attrs):
    return SayouNode(
        node_id=f"sayou:func:{path.replace('/', '_')}::{name}",
        node_class=SayouClass.FUNCTION,
        attributes={
            SayouAttribute.FILE_PATH: path,
            SayouAttribute.SYMBOL_NAME: name,
            **attrs,
        },
    )


def _block(idx=0, path=SRC, **attrs):
    return SayouNode(
        node_id=f"sayou:block:{path.replace('/', '_')}::{idx}",
        node_class=SayouClass.CODE_BLOCK,
        attributes={SayouAttribute.FILE_PATH: path, **attrs},
    )


nodes = [
    # ── base_normalizer.py ───────────────────────────────────────────
    _file(SRC2, **{SayouAttribute.MODULE_ALL_RAW: ["BaseNormalizer"]}),
    _class("BaseNormalizer", path=SRC2),
    _method(
        "normalize",
        "BaseNormalizer",
        path=SRC2,
        **{SayouAttribute.RAISES_RAW: ["NotImplementedError"]},
    ),
    _method(
        "_do_normalize",
        "BaseNormalizer",
        path=SRC2,
        **{SayouAttribute.DECORATORS_RAW: ["abstractmethod"]},
    ),
    # ── pipeline.py ──────────────────────────────────────────────────
    _file(
        SRC,
        **{
            SayouAttribute.MODULE_ALL_RAW: ["RefineryPipeline"],
            "sayou:importsRaw": [
                {"module": "base_normalizer", "name": "BaseNormalizer", "level": 1},
            ],
        },
    ),
    _block(
        0,
        path=SRC,
        **{
            SayouAttribute.MODULE_VARS_RAW: ["COMPONENT_REGISTRY"],
            "sayou:importsRaw": [
                {"module": "base_normalizer", "name": "BaseNormalizer", "level": 1},
            ],
        },
    ),
    _class(
        "RefineryPipeline",
        path=SRC,
        **{
            SayouAttribute.INHERITS_FROM_RAW: ["BaseNormalizer"],
        },
    ),
    _method(
        "__init__",
        "RefineryPipeline",
        path=SRC,
        **{
            SayouAttribute.CALLS_RAW: ["super", "_register"],
            SayouAttribute.PARAMS_RAW: [
                {"name": "self"},
                {"name": "extra_normalizers", "has_default": True},
            ],
        },
    ),
    _method(
        "run",
        "RefineryPipeline",
        path=SRC,
        **{
            SayouAttribute.CALLS_RAW: ["_resolve_normalizer"],
            SayouAttribute.TYPE_REFS_RAW: ["BaseNormalizer"],
            SayouAttribute.RAISES_RAW: ["RefineryError"],
            SayouAttribute.RETURN_TYPE: "List[SayouBlock]",
        },
    ),
    _method(
        "_resolve_normalizer",
        "RefineryPipeline",
        path=SRC,
        **{
            SayouAttribute.GLOBALS_DECLARED_RAW: ["COMPONENT_REGISTRY"],
            SayouAttribute.RETURN_TYPE: "Optional[Type[BaseNormalizer]]",
        },
    ),
    _func(
        "_load_module",
        path=SRC,
        **{
            SayouAttribute.CALLS_RAW: ["importlib.import_module"],
        },
    ),
]

output = SayouOutput(nodes=nodes, metadata={"source": SRC})


# ── Build the Code Graph
"""
Pass with ``strategy="CodeGraphBuilder"``.  Returns:

    {
        "nodes": [<node dicts>],
        "edges": [<edge dicts with confidence + resolution>],
        "metadata": { … },
    }
"""
result = pipeline.run(output, strategy="CodeGraphBuilder")

all_edges = result["edges"]
print("=== Build the Code Graph ===")
print(f"  Nodes input  : {len(nodes)}")
print(f"  Edges output : {len(all_edges)}")
print()
by_type = {}
for e in all_edges:
    by_type.setdefault(e["type"], []).append(e)
for pred, es in sorted(by_type.items()):
    print(f"  {pred:30s} × {len(es)}")


# ── CONTAINS (structural)
"""
FILE → CLASS/FUNC/BLOCK edges are generated automatically from each
node's ``sayou:filePath`` attribute — no explicit relationship needed.
"""
print("\n=== CONTAINS edges ===")
for e in by_type.get(SayouPredicate.CONTAINS, []):
    src = (
        e["source"].split("::")[-1]
        if "::" in e["source"]
        else e["source"].split("_")[-1]
    )
    tgt = e["target"].split("::")[-1] if "::" in e["target"] else e["target"]
    if e.get(SayouEdgeMeta.EDGE_SOURCE) == "structural":
        print(f"  {src} → {tgt}")


# ── CALLS (direct, HIGH confidence)
"""
``calls_raw`` lists from language splitters are resolved against the
symbol index.  Resolution priority:
  1. Sibling method in the same class  (intra-class self.foo())
  2. Same-file function
  3. Globally unique symbol across all files
Unresolvable names produce no edge (no phantom nodes).
"""
print("\n=== CALLS edges (HIGH confidence) ===")
for e in by_type.get(SayouPredicate.CALLS, []):
    src = e["source"].split("::")[-1]
    tgt = e["target"].split("::")[-1]
    conf = e.get(SayouEdgeMeta.CONFIDENCE, "?")
    mismatch = " [ASYNC MISMATCH]" if e.get("async_mismatch") else ""
    print(f"  {src:30s} → {tgt}  ({conf}){mismatch}")


# ── INHERITS
"""
``inherits_from_raw`` is resolved first in the same file, then globally.
Only unambiguous names produce an INHERITS edge.
"""
print("\n=== INHERITS edges ===")
for e in by_type.get(SayouPredicate.INHERITS, []):
    src = e["source"].split("::")[-1]
    tgt = e["target"].split("::")[-1]
    print(f"  {src} → {tgt}  ({e[SayouEdgeMeta.CONFIDENCE]})")


# ── RAISES (virtual exception nodes)
"""
Each raised exception type becomes a virtual node ``sayou:exc:<TypeName>``.
The same virtual node is reused across all functions that raise the same
type, enabling queries like "which functions raise ValueError?".
"""
print("\n=== RAISES edges ===")
for e in by_type.get(SayouPredicate.RAISES, []):
    src = e["source"].split("::")[-1]
    exc = e["target"]
    print(f"  {src} raises {exc}")


# ── USES_TYPE (annotation / isinstance)
"""
USES_TYPE is MEDIUM confidence (INFERRED) because a type annotation does
not guarantee the function actually calls the class — it may be used only
as a type hint.
"""
print("\n=== USES_TYPE edges ===")
for e in by_type.get(SayouPredicate.USES_TYPE, []):
    src = e["source"].split("::")[-1]
    tgt = e["target"].split("::")[-1]
    conf = e[SayouEdgeMeta.CONFIDENCE]
    res = e[SayouEdgeMeta.RESOLUTION]
    print(f"  {src:30s} uses_type {tgt}  ({conf} / {res})")


# ── MUTATES_GLOBAL
"""
Functions declaring ``global x`` are linked to the CODE_BLOCK node that
defines ``x`` at module level.  If the variable is defined in another
package, no phantom node is created — the edge is silently skipped.
"""
print("\n=== MUTATES_GLOBAL edges ===")
for e in by_type.get(SayouPredicate.MUTATES_GLOBAL, []):
    src = e["source"].split("::")[-1]
    tgt = e["target"].split("::")[-1]
    print(f"  {src} mutates_global {tgt}")


# ── EXPOSES (__all__)
"""
FILE → FUNC/CLASS edges for symbols declared in ``__all__`` mark the
public interface of a module.
"""
print("\n=== EXPOSES edges ===")
for e in by_type.get(SayouPredicate.EXPOSES, []):
    src = e["source"].split("_")[-1]
    tgt = e["target"].split("::")[-1]
    print(f"  {src} exposes {tgt}")


# ── Edge metadata (confidence + resolution)
"""
Every edge carries three standard metadata keys (SayouEdgeMeta):

    confidence  — "HIGH" | "MEDIUM" | "LOW"
    resolution  — "DIRECT" | "INFERRED" | "HEURISTIC"
    edge_source — which resolver generated this edge

Use these for filtering in downstream graph queries:

    MATCH (a)-[r:CALLS]->(b)
    WHERE r.confidence = 'HIGH'
    RETURN a, b
"""
print("\n=== Edge Metadata Sample ===")
sample = next((e for e in all_edges if e["type"] == SayouPredicate.CALLS), None)
if sample:
    print(f"  type       : {sample['type']}")
    print(f"  confidence : {sample[SayouEdgeMeta.CONFIDENCE]}")
    print(f"  resolution : {sample[SayouEdgeMeta.RESOLUTION]}")
    print(f"  edge_source: {sample[SayouEdgeMeta.EDGE_SOURCE]}")


# ── Save Results
with open("code_graph_output.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False, default=str)

print(
    f"\nSaved code graph ({len(result['nodes'])} nodes, "
    f"{len(all_edges)} edges) to 'code_graph_output.json'"
)
