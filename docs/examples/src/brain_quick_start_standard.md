!!! abstract "Source"
    Synced from [`packages/sayou-brain/examples/quick_start_standard.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-brain/examples/quick_start_standard.py).

## Setup

Build a document RAG knowledge base using `StandardPipeline`.

`StandardPipeline` is the all-in-one Brain for document ingestion.
It automates the full journey from raw files to a searchable knowledge
store — parsing, normalisation, chunking, semantic wrapping, graph/vector
assembly, and persistence — in a single call.

Flow
────
Connector → Document → Refinery → Chunking → Wrapper → Assembler → Loader

Use cases
─────────
- RAG knowledge base from PDFs, DOCX, HTML pages
- Multi-source document ingestion into a vector store
- Enterprise knowledge graph over mixed document types

```python
from unittest.mock import MagicMock, patch

from sayou.core.schemas import SayouChunk, SayouNode, SayouOutput

from sayou.brain.pipelines.standard import StandardPipeline
```

## Sample Packets

StandardPipeline reads packet.task.meta["filename"] to identify each file.
We build lightweight packet objects that satisfy this interface.

```python
class _Packet:
    """Minimal packet object compatible with StandardPipeline's expectations."""

    def __init__(self, filename, data, success=True, error=None):
        self.data = data
        self.success = success
        self.error = error
        self.meta = {"filename": filename}
        self.task = MagicMock()
        self.task.meta = {"filename": filename}


doc_packets = [
    _Packet("q1_report.pdf", b"%PDF-1.4 ... Q1 report binary ..."),
    _Packet("architecture.docx", b"PK\x03\x04 ... DOCX binary ..."),
    _Packet("classified.pdf", None, success=False, error="403 Forbidden"),
]
```

## Stage Stubs

Deterministic stubs trace each stage.  The output is meaningful without
installing any sub-library.

```python
doc_log = []
refinery_log = []
chunk_idx = [0]
node_idx = [0]


def parse_document(data, filename, **kw):
    doc_type = "pdf" if filename.endswith(".pdf") else "docx"
    doc_log.append(f"{filename} → {doc_type}")
    doc = MagicMock()
    doc.type = doc_type
    doc.metadata = {"source": filename}
    return doc


def refine(data, **kw):
    if hasattr(data, "type"):  # document object
        fname = data.metadata.get("source", "doc")
        text = f"Extracted text from {fname}."
    else:
        text = str(data)[:60]
    blk = MagicMock()
    blk.type = "text"
    blk.content = text
    blk.metadata = {}
    refinery_log.append(text[:50])
    return [blk]


def chunk(blocks, **kw):
    result = []
    for blk in blocks:
        chunk_idx[0] += 1
        result.append(
            SayouChunk(
                content=blk.content,
                metadata={"chunk_id": f"c{chunk_idx[0]:03d}"},
            )
        )
    return result


def wrap(chunks, **kw):
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
    return SayouOutput(nodes=nodes)


def assemble(sayou_output, **kw):
    return [
        {
            "id": n.node_id,
            "vector": [0.1, 0.2, 0.3, 0.4],
            "text": n.attributes.get("schema:text", ""),
        }
        for n in sayou_output.nodes
    ]
```

## Run the Pipeline

```python
mock_connector = MagicMock()
mock_connector.run.return_value = iter(doc_packets)
mock_document = MagicMock()
mock_document.run.side_effect = parse_document
mock_refinery = MagicMock()
mock_refinery.run.side_effect = refine
mock_chunking = MagicMock()
mock_chunking.run.side_effect = chunk
mock_wrapper = MagicMock()
mock_wrapper.run.side_effect = wrap
mock_assembler = MagicMock()
mock_assembler.run.side_effect = assemble
mock_loader = MagicMock()
mock_loader.run.return_value = True

pipeline = StandardPipeline()
with patch.object(pipeline, "connector", mock_connector), patch.object(
    pipeline, "document", mock_document
), patch.object(pipeline, "refinery", mock_refinery), patch.object(
    pipeline, "chunking", mock_chunking
), patch.object(
    pipeline, "wrapper", mock_wrapper
), patch.object(
    pipeline, "assembler", mock_assembler
), patch.object(
    pipeline, "loader", mock_loader
):

    stats = pipeline.ingest(
        "s3://my-docs/",
        destination="chroma://./chroma_db/sayou_docs",
        strategies={
            "connector": "s3",
            "refinery": "standard_doc",
            "chunking": "markdown",
            "wrapper": "document_chunk",
            "assembler": "VectorBuilder",
            "loader": "ChromaWriter",
        },
    )

print("=== StandardPipeline Run ===")
print(f"  Files total   : {stats['files_count']}")
print(f"  Processed     : {stats['processed']}")
print(f"  Failed        : {stats['failed']}  (classified.pdf → 403)")
```

## Stage-by-stage Trace

Stages 2–5 (Document → Wrapper) run per file.
Stage 6 (Assembler) runs once on all accumulated nodes.

```python
print("\n=== Stage-by-stage Trace ===")
print(f"  {'File':25s}  Document           Refinery output")
print(f"  {'-'*72}")
for doc_entry, ref_entry in zip(doc_log, refinery_log):
    filename, doc_type = doc_entry.split(" → ")
    print(f"  {filename:25s}  parsed as {doc_type:6s}   {ref_entry!r}")
```

## Vector Payloads

VectorBuilder receives all accumulated nodes at once and returns
a list of vector payloads ready for ChromaDB / Elasticsearch.

```python
asm_call = mock_assembler.run.call_args
asm_input = asm_call.args[0] if asm_call.args else asm_call.kwargs.get("input_data")
payloads = assemble(asm_input) if asm_input else []

print("\n=== Vector Payloads (sent to ChromaWriter) ===")
print(f"  Total payloads: {len(payloads)}")
for p in payloads:
    print(f"  [{p['id']}]")
    print(f"    text   = {p['text']!r}")
    print(f"    vector = {p['vector']}  (dim={len(p['vector'])})")
```

## Binary Document Handling

Binary detection: isinstance(packet.data, bytes)

Fallback chain:
  bytes → DocumentPipeline → ok    → Refinery  (normal path)
  bytes → DocumentPipeline fails   → UTF-8 decode → Refinery
  bytes → UTF-8 decode fails       → skip  (stats["failed"]++)

```python
print("\n=== Binary Handling Fallback Chain ===")
print("  bytes → Document → Refinery           (normal path)")
print("  bytes → Document fails → UTF-8 decode → Refinery")
print("  bytes → decode fails                  → skip  (failed++)")
```

## Stats

```python
print("\n=== Stats ===")
print(f"  files_count = {stats['files_count']}  (total packets from Connector)")
print(f"  processed   = {stats['processed']}  (successfully reached Wrapper)")
print(f"  failed      = {stats['failed']}  (403 Forbidden packet)")
```