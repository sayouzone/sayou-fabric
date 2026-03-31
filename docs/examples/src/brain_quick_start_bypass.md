!!! abstract "Source"
    Synced from [`packages/sayou-brain/examples/quick_start_bypass.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-brain/examples/quick_start_bypass.py).

## Sub-library stubs

```python
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
```

## Setup

Mirror raw data from any source to a destination using `BypassPipeline`.

`BypassPipeline` applies zero transformation — every packet that comes
out of the Connector is written directly to the Loader exactly as received.

Flow
────
Connector → Loader  (no intermediate stages)

Use cases
─────────
- Raw file backup / archiving  (PDFs, images, binaries as-is)
- Database record migration with no schema change
- Log shipping to cold storage
- Staging: collect raw data first, process later

Comparison with TransferPipeline
─────────────────────────────────
``TransferPipeline`` optionally runs data through ``RefineryPipeline``.
``BypassPipeline`` makes no such option available — fidelity to the
original payload is the only goal.

```python
from sayou.brain.pipelines.bypass import BypassPipeline
from sayou.core.schemas import SayouPacket
```

## Sample Packets

In production these come from ConnectorPipeline.
Each SayouPacket carries the raw payload and metadata.

``meta["filename"]`` drives output path resolution when destination
is a directory.

```python
raw_packets = [
    SayouPacket(
        data=b"%PDF-1.4 ... binary content ...",
        success=True,
        meta={"filename": "report_q1.pdf"},
    ),
    SayouPacket(
        data=b"\x89PNG\r\n binary image", success=True, meta={"filename": "diagram.png"}
    ),
    SayouPacket(
        data=b'{"records": [1, 2, 3]}', success=True, meta={"filename": "export.json"}
    ),
    SayouPacket(
        data=None,
        success=False,
        error="Connection timeout",
        meta={"filename": "missing.csv"},
    ),
]
```

## Basic Bypass

Each successful packet is written verbatim to the destination directory.

Output filename priority: filename → subject → title → uid → file_<index>

```python
mock_connector = MagicMock()
mock_connector.run.return_value = iter(raw_packets)
mock_loader = MagicMock()
mock_loader.run.return_value = True

pipeline = BypassPipeline()
with patch.object(pipeline, "connector", mock_connector), patch.object(
    pipeline, "loader", mock_loader
):
    stats = pipeline.ingest(
        "file:///data/archive/",
        destination="./output/archive/",
        strategies={"connector": "file", "loader": "FileWriter"},
    )

print("=== Basic Bypass ===")
print(f"  Read    : {stats['read']}")
print(f"  Written : {stats['written']}")
print(f"  Failed  : {stats['failed']}  (1 timed-out packet expected)")

write_calls = mock_loader.run.call_args_list
print(f"\n  Loader.run() called {len(write_calls)} time(s):")
for c in write_calls:
    dest = c.kwargs.get("destination") or (c.args[1] if len(c.args) > 1 else "?")
    data = c.kwargs.get("input_data") or (c.args[0] if c.args else None)
    preview = data[:20] if isinstance(data, bytes) else str(data)[:20]
    import os

    print(f"    → {os.path.basename(dest):25s}  payload={preview!r}…")
```

## Output Path Resolution

``_resolve_output_path`` derives a filename from packet metadata.

- Destination with extension → single-file mode (all packets → same file)
- Destination without extension → directory mode (one file per packet)

```python
print("\n=== Output Path Resolution ===")
for i, pkt in enumerate(raw_packets[:3]):
    resolved = pipeline._resolve_output_path("./out/", pkt, i)
    fname = pkt.meta.get("filename", f"file_{i}")
    print(f"  packet[{i}] filename={fname:20s} → {resolved}")
```

## Failure Isolation

Failed packets (success=False) are counted in stats["failed"] but
do not stop the pipeline.  Remaining packets are still processed.

```python
mixed = [
    SayouPacket(data=b"ok1", success=True, meta={"filename": "a.bin"}),
    SayouPacket(
        data=None, success=False, error="read error", meta={"filename": "b.bin"}
    ),
    SayouPacket(data=b"ok2", success=True, meta={"filename": "c.bin"}),
]
mock_c2 = MagicMock()
mock_c2.run.return_value = iter(mixed)
mock_l2 = MagicMock()
mock_l2.run.return_value = True

pipeline2 = BypassPipeline()
with patch.object(pipeline2, "connector", mock_c2), patch.object(
    pipeline2, "loader", mock_l2
):
    stats2 = pipeline2.ingest("src://x", destination="./out/")

print("\n=== Failure Isolation ===")
print(
    f"  read={stats2['read']}  written={stats2['written']}  failed={stats2['failed']}"
)
print(f"  b.bin failed → a.bin and c.bin still written")
```

## BypassPipeline vs TransferPipeline

BypassPipeline   — Connector → Loader              (payload untouched)
TransferPipeline — Connector → [Refinery] → Loader (optional normalisation)

```python
print("\n=== BypassPipeline vs TransferPipeline ===")
rows = [
    ("Refinery stage", "None", "Optional (use_refinery=True)"),
    ("Payload fidelity", "Verbatim", "May be transformed"),
    ("Binary safe", "Yes", "Depends on normalizer"),
    ("Use case", "Archive", "ETL / migration"),
]
print(f"  {'Feature':22s}  {'Bypass':20s}  TransferPipeline")
print(f"  {'-'*65}")
for label, b, t in rows:
    print(f"  {label:22s}  {b:20s}  {t}")
```