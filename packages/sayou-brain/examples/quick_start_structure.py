import sys
import types as _types
from unittest.mock import MagicMock, patch

# ── Sub-library stubs
_sayou = _types.ModuleType("sayou")
_sayou.__path__ = [
    "/home/claude/brain_pkg/src/sayou",
    "/home/claude/core_pkg/src/sayou",
]
sys.modules["sayou"] = _sayou
sys.path.insert(0, "/home/claude/brain_pkg/src/sayou/../..")
sys.path.insert(0, "/home/claude/core_pkg/src/sayou/../..")


def _stub(module, cls_name):
    mod = _types.ModuleType(module)
    cls = type(
        cls_name,
        (),
        {
            "__init__": lambda self, **kw: None,
            "initialize": lambda self, **kw: None,
            "run": lambda self, *a, **kw: None,
            "add_callback": lambda self, cb: None,
        },
    )
    setattr(mod, cls_name, cls)
    sys.modules[module] = mod
    setattr(_sayou, module.split(".")[-1], mod)


for _m, _c in [
    ("sayou.connector", "ConnectorPipeline"),
    ("sayou.document", "DocumentPipeline"),
    ("sayou.refinery", "RefineryPipeline"),
    ("sayou.chunking", "ChunkingPipeline"),
    ("sayou.wrapper", "WrapperPipeline"),
    ("sayou.assembler", "AssemblerPipeline"),
    ("sayou.loader", "LoaderPipeline"),
]:
    _stub(_m, _c)

# ── Setup
"""
Build a code knowledge graph from source files using `StructurePipeline`.

`StructurePipeline` is purpose-built for code intelligence workloads.
It collects source files, splits them into typed nodes (File, Class,
Method, Function, …), assembles a fully linked knowledge graph with
confidence-annotated edges (CALLS, INHERITS, OVERRIDES, …), and persists
the result to a graph or vector store.

Flow
────
Connector → Chunking → Wrapper → Assembler → Loader

Use cases
─────────
- Code knowledge graph for a RAG-based code assistant
- Dependency / call-graph analysis across a codebase
- Automated architecture documentation
"""
from sayou.core.schemas import SayouChunk, SayouNode, SayouOutput, SayouPacket

from sayou.brain.pipelines.structure import StructurePipeline

# ── Sample Source Files
"""
Simulating a GitHub Connector fetching two Python files.
Each packet carries the file content via the data dict.
"""
source_packets = [
    SayouPacket(
        data={
            "content": "class Pipeline:\n    def run(self): pass",
            "meta": {"source": "sayou/pipeline.py", "extension": ".py"},
        },
        success=True,
        meta={"filename": "sayou/pipeline.py"},
    ),
    SayouPacket(
        data={
            "content": "class BaseComponent:\n    def initialize(self): pass",
            "meta": {"source": "sayou/base.py", "extension": ".py"},
        },
        success=True,
        meta={"filename": "sayou/base.py"},
    ),
]


# ── Chunking Stub
"""
PythonSplitter produces typed chunks (class_header, method, …).
Here we return two chunks per file for clarity.
"""
CHUNK_SETS = [
    [
        SayouChunk(
            content="class Pipeline:",
            metadata={
                "semantic_type": "class_header",
                "class_name": "Pipeline",
                "source": "sayou/pipeline.py",
                "language": "python",
            },
        ),
        SayouChunk(
            content="    def run(self): pass",
            metadata={
                "semantic_type": "method",
                "function_name": "run",
                "parent_node": "Pipeline",
                "source": "sayou/pipeline.py",
                "language": "python",
            },
        ),
    ],
    [
        SayouChunk(
            content="class BaseComponent:",
            metadata={
                "semantic_type": "class_header",
                "class_name": "BaseComponent",
                "source": "sayou/base.py",
                "language": "python",
            },
        ),
        SayouChunk(
            content="    def initialize(self): pass",
            metadata={
                "semantic_type": "method",
                "function_name": "initialize",
                "parent_node": "BaseComponent",
                "source": "sayou/base.py",
                "language": "python",
            },
        ),
    ],
]
chunk_iter = iter(CHUNK_SETS)


# ── Wrapper Stub
"""
CodeChunkAdapter maps chunks to typed SayouNodes with stable symbol-based IDs.
"""


def make_nodes(source, class_name, method_name):
    safe = source.replace("/", "_")
    return SayouOutput(
        nodes=[
            SayouNode(
                node_id=f"sayou:file:{safe}",
                node_class="sayou:File",
                attributes={"sayou:filePath": source},
            ),
            SayouNode(
                node_id=f"sayou:class:{safe}::{class_name}",
                node_class="sayou:Class",
                attributes={"sayou:symbolName": class_name, "sayou:filePath": source},
            ),
            SayouNode(
                node_id=f"sayou:method:{safe}::{class_name}.{method_name}",
                node_class="sayou:Method",
                attributes={
                    "sayou:symbolName": method_name,
                    "sayou:parentClass": class_name,
                    "sayou:filePath": source,
                },
            ),
        ]
    )


WRAPPER_OUTPUTS = [
    make_nodes("sayou/pipeline.py", "Pipeline", "run"),
    make_nodes("sayou/base.py", "BaseComponent", "initialize"),
]
wrapper_iter = iter(WRAPPER_OUTPUTS)


# ── Assembler Stub
"""
CodeGraphBuilder resolves cross-file edges (CALLS, INHERITS, …) and
returns a graph dict with nodes + typed, confidence-annotated edges.
"""


def assemble(sayou_output, **kw):
    nodes = sayou_output.nodes
    edges = [
        {
            "source": f"sayou:method:sayou_pipeline_py::Pipeline.run",
            "target": f"sayou:method:sayou_base_py::BaseComponent.initialize",
            "type": "sayou:calls",
            "confidence": "HIGH",
            "resolution": "DIRECT",
        },
        {
            "source": f"sayou:class:sayou_pipeline_py::Pipeline",
            "target": f"sayou:class:sayou_base_py::BaseComponent",
            "type": "sayou:inherits",
            "confidence": "HIGH",
            "resolution": "DIRECT",
        },
    ]
    return {"nodes": [n.model_dump() for n in nodes], "edges": edges, "metadata": {}}


# ── Run the Pipeline
mock_connector = MagicMock()
mock_connector.run.return_value = iter(source_packets)
mock_chunking = MagicMock()
mock_chunking.run.side_effect = lambda *a, **kw: next(chunk_iter, [])
mock_wrapper = MagicMock()
mock_wrapper.run.side_effect = lambda *a, **kw: next(wrapper_iter, SayouOutput())
mock_assembler = MagicMock()
mock_assembler.run.side_effect = assemble
mock_loader = MagicMock()
mock_loader.run.return_value = True

pipeline = StructurePipeline()
with patch.object(pipeline, "connector", mock_connector), patch.object(
    pipeline, "chunking", mock_chunking
), patch.object(pipeline, "wrapper", mock_wrapper), patch.object(
    pipeline, "assembler", mock_assembler
), patch.object(
    pipeline, "loader", mock_loader
):

    stats = pipeline.ingest(
        "github://owner/sayou",
        destination="bolt://localhost:7687",
        strategies={
            "connector": "github",
            "chunking": "python",
            "wrapper": "code_chunk",
            "assembler": "CodeGraphBuilder",
            "loader": "Neo4jWriter",
        },
    )

print("=== StructurePipeline Run ===")
print(f"  Files extracted : {stats['extracted']}")
print(f"  Total chunks    : {stats['chunks']}")
print(f"  Nodes assembled : {stats['nodes']}")
print(f"  Edges resolved  : {stats['edges']}")
print(f"  Saved           : {stats['saved']}")


# ── Assembled Graph
asm_call = mock_assembler.run.call_args
asm_input = asm_call.args[0] if asm_call.args else asm_call.kwargs.get("input_data")
graph = assemble(asm_input)

print("\n=== Assembled Graph ===")
print(f"  Nodes ({len(graph['nodes'])}):")
for n in graph["nodes"]:
    cls = n["node_class"].split(":")[-1]
    nid = n["node_id"].split("::")[-1]
    print(f"    [{cls:15s}] {nid}")

print(f"\n  Edges ({len(graph['edges'])}):")
for e in graph["edges"]:
    src = e["source"].split("::")[-1]
    tgt = e["target"].split("::")[-1]
    pred = e["type"].split(":")[-1]
    conf = e["confidence"]
    print(f"    {src:30s} --[{pred:8s}]--> {tgt}  ({conf})")


# ── Strategy Selection Guide
print("\n=== Strategy Selection Guide ===")
rows = [
    ("Python code", '"python"', '"code_chunk"', '"CodeGraphBuilder"'),
    ("JS/TS code", '"js"', '"code_chunk"', '"CodeGraphBuilder"'),
    ("Markdown", '"markdown"', '"document_chunk"', '"GraphBuilder"'),
    ("Generic", '"auto"', '"auto"', '"auto"'),
]
print(f"  {'Source':12s}  {'chunking':14s}  {'wrapper':18s}  assembler")
print(f"  {'-'*64}")
for src, chk, wrp, asm in rows:
    print(f"  {src:12s}  {chk:14s}  {wrp:18s}  {asm}")
