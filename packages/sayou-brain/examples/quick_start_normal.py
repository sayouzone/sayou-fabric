from unittest.mock import MagicMock, patch

# ── Setup
"""
Build a knowledge graph with Refinery normalisation using `NormalPipeline`.

`NormalPipeline` sits between `StructurePipeline` (no Refinery) and
`StandardPipeline` (adds Document parsing for binary files).  Use it
when raw connector output needs normalisation before chunking — for
example HTML stripping, JSON flattening, or mixed text/code sources.

Flow
────
Connector → Refinery → Chunking → Wrapper → Assembler → Loader

Pipeline Comparison
───────────────────
StructurePipeline — no Refinery (code sources, already clean)
NormalPipeline    — adds Refinery before Chunking
StandardPipeline  — adds Document parsing for binary files (PDF, DOCX, …)
"""
from sayou.core.schemas import SayouChunk, SayouNode, SayouOutput, SayouPacket

from sayou.brain.pipelines.normal import NormalPipeline

# ── Sample HTML Packets
"""
Simulating a Connector that fetches HTML documentation pages.
These need Refinery (html strategy) to strip tags before chunking.
"""
html_packets = [
    SayouPacket(
        data="<h1>Introduction</h1><p>Sayou Fabric is a modular pipeline.</p>",
        success=True,
        meta={"filename": "intro.html"},
    ),
    SayouPacket(
        data="<h2>Architecture</h2><p>Eight libraries coordinate via Brain.</p>",
        success=True,
        meta={"filename": "architecture.html"},
    ),
    SayouPacket(
        data="<h2>Chunking</h2><p>Splits blocks into retrieval-ready pieces.</p>",
        success=True,
        meta={"filename": "chunking.html"},
    ),
]


# ── Stage Stubs
"""
Each sub-pipeline stub returns realistic Sayou schema objects so the
output is meaningful without a real installation.
"""
refinery_log = []


def refinery_side(data, **kw):
    import re

    clean = re.sub(r"<[^>]+>", "", str(data)).strip()
    refinery_log.append(clean[:50])
    blk = MagicMock()
    blk.type = "text"
    blk.content = clean
    blk.metadata = {}
    return [blk]


chunk_idx = [0]
chunking_log = []


def chunking_side(blocks, **kw):
    result = []
    for blk in blocks:
        words = blk.content.split()
        mid = max(1, len(words) // 2)
        for part in [words[:mid], words[mid:]]:
            chunk_idx[0] += 1
            result.append(
                SayouChunk(
                    content=" ".join(part),
                    metadata={"chunk_id": f"c{chunk_idx[0]:03d}"},
                )
            )
    chunking_log.append(len(result))
    return result


node_idx = [0]
wrapper_log = []


def wrapper_side(chunks, **kw):
    nodes = []
    for ch in chunks:
        node_idx[0] += 1
        nodes.append(
            SayouNode(
                node_id=f"sayou:doc:n{node_idx[0]:03d}",
                node_class="sayou:TextFragment",
                attributes={"schema:text": ch.content},
            )
        )
    wrapper_log.append(len(nodes))
    return SayouOutput(nodes=nodes)


assembly_result = {"nodes": [], "edges": [], "metadata": {}}


# ── Run the Pipeline
mock_connector = MagicMock()
mock_connector.run.return_value = iter(html_packets)
mock_refinery = MagicMock()
mock_refinery.run.side_effect = refinery_side
mock_chunking = MagicMock()
mock_chunking.run.side_effect = chunking_side
mock_wrapper = MagicMock()
mock_wrapper.run.side_effect = wrapper_side
mock_assembler = MagicMock()
mock_assembler.run.return_value = assembly_result
mock_loader = MagicMock()
mock_loader.run.return_value = True

pipeline = NormalPipeline()
with patch.object(pipeline, "connector", mock_connector), patch.object(
    pipeline, "refinery", mock_refinery
), patch.object(pipeline, "chunking", mock_chunking), patch.object(
    pipeline, "wrapper", mock_wrapper
), patch.object(
    pipeline, "assembler", mock_assembler
), patch.object(
    pipeline, "loader", mock_loader
):

    stats = pipeline.ingest(
        "https://docs.example.com/",
        destination="bolt://localhost:7687",
        strategies={
            "connector": "http",
            "refinery": "html",
            "chunking": "markdown",
            "wrapper": "document_chunk",
            "assembler": "GraphBuilder",
            "loader": "Neo4jWriter",
        },
    )

print("=== NormalPipeline Run ===")
print(f"  Packets extracted : {stats['extracted']}")
print(f"  Total chunks      : {stats['chunks']}")
print(f"  Nodes collected   : {stats['nodes']}")
print(f"  Edges assembled   : {stats['edges']}")
print(f"  Saved             : {stats['saved']}")


# ── Per-packet Stage Trace
"""
Each packet flows through Refinery → Chunking → Wrapper independently.
Nodes are accumulated in memory before Assembler runs once globally.
"""
print("\n=== Per-packet Stage Trace ===")
for i, (pkt, refined, n_chunks, n_nodes) in enumerate(
    zip(html_packets, refinery_log, chunking_log, wrapper_log)
):
    fname = pkt.meta["filename"]
    print(
        f"  [{i+1}] {fname:22s}"
        f"  refinery→ {refined!r:38s}"
        f"  chunks={n_chunks}  nodes={n_nodes}"
    )


# ── Global Assembly
"""
After all packets are processed, the accumulated SayouNodes are passed
to AssemblerPipeline as a single SayouOutput.  This enables cross-document
edge resolution impossible in a per-packet assembly loop.
"""
asm_call = mock_assembler.run.call_args
asm_input = asm_call.args[0] if asm_call.args else asm_call.kwargs.get("input_data")
print("\n=== Global Assembly ===")
print(f"  AssemblerPipeline.run() called once")
print(
    f"  Input: SayouOutput with {len(asm_input.nodes)} node(s) "
    f"(accumulated from all {len(html_packets)} files)"
)
print(f"  Strategy: GraphBuilder → Loader receives assembled graph dict")


# ── Pipeline Comparison
print("\n=== Pipeline Comparison ===")
rows = [
    ("Connector", "yes", "yes", "yes"),
    ("Document", "—", "—", "yes"),
    ("Refinery", "—", "yes", "yes"),
    ("Chunking", "yes", "yes", "yes"),
    ("Wrapper", "yes", "yes", "yes"),
    ("Assembler", "yes", "yes", "yes"),
    ("Loader", "yes", "yes", "yes"),
]
print(f"  {'Stage':12s}  {'Structure':10s}  {'Normal':10s}  Standard")
print(f"  {'-'*48}")
for stage, s, n, std in rows:
    print(f"  {stage:12s}  {s:10s}  {n:10s}  {std}")
