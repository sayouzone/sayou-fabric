!!! abstract "Source"
    Synced from [`packages/sayou-brain/examples/quick_start_transfer.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-brain/examples/quick_start_transfer.py).

## Setup

ETL pipeline with optional normalisation using `TransferPipeline`.

`TransferPipeline` fetches raw data from any Connector source, optionally
normalises it through RefineryPipeline, and writes each item to the
destination as it arrives — streaming, not batch.

Flow
────
Connector → [RefineryPipeline] → Loader

Use cases
─────────
- Database record migration with light schema normalisation
- Log backup with optional content filtering
- Raw data archiving with Refinery preprocessing

```python
from sayou.core.schemas import SayouPacket

from sayou.brain.pipelines.transfer import TransferPipeline
```

## Sample Data

Simulating a Connector that fetches three JSON records from an API
and one that fails mid-transfer.

```python
api_packets = [
    SayouPacket(
        data={"id": "r001", "content": "<h1>Sales</h1><p>Revenue: $1.2M</p>"},
        success=True,
        meta={"filename": "r001.json"},
    ),
    SayouPacket(
        data={"id": "r002", "content": "<p>Discussed roadmap for Q2.</p>"},
        success=True,
        meta={"filename": "r002.json"},
    ),
    SayouPacket(
        data=None, success=False, error="404 Not Found", meta={"filename": "r003.json"}
    ),
    SayouPacket(
        data={"id": "r004", "content": "Raw budget data for FY2025."},
        success=True,
        meta={"filename": "r004.json"},
    ),
]
```

## Transfer Without Refinery

Default mode: Connector → Loader, no transformation.
Each successful packet is written verbatim.

```python
mock_connector = MagicMock()
mock_connector.run.return_value = iter(api_packets)
mock_loader = MagicMock()
mock_loader.run.return_value = True

pipeline = TransferPipeline()
with patch.object(pipeline, "connector", mock_connector), patch.object(
    pipeline, "loader", mock_loader
):
    stats = pipeline.ingest(
        "api://records",
        destination="./output/raw/",
        strategies={"loader": "JsonLineWriter"},
    )

print("=== Transfer Without Refinery ===")
print(f"  read={stats['read']}  written={stats['written']}  failed={stats['failed']}")
print(f"  (r003 failed, the other 3 written as-is)")
```

## Transfer With Refinery

Set ``use_refinery=True`` to normalise each packet before writing.

If Refinery returns an empty result, the packet is skipped —
this enables content-based filtering.

```python
REFINED = [
    [MagicMock(type="text", content="Sales. Revenue: $1.2M", metadata={})],
    [MagicMock(type="text", content="Discussed roadmap for Q2.", metadata={})],
    [MagicMock(type="text", content="Raw budget data for FY2025.", metadata={})],
]
refinery_iter = iter(REFINED)

mock_c2 = MagicMock()
mock_c2.run.return_value = iter(api_packets)
mock_r2 = MagicMock()
mock_r2.run.side_effect = lambda data, **kw: next(refinery_iter, [])
mock_l2 = MagicMock()
mock_l2.run.return_value = True

pipeline2 = TransferPipeline()
with patch.object(pipeline2, "connector", mock_c2), patch.object(
    pipeline2, "refinery", mock_r2
), patch.object(pipeline2, "loader", mock_l2):
    stats2 = pipeline2.ingest(
        "api://records",
        destination="./output/normalised/",
        use_refinery=True,
        strategies={"refinery": "html", "loader": "FileWriter"},
    )

print("\n=== Transfer With Refinery ===")
print(
    f"  read={stats2['read']}  written={stats2['written']}  failed={stats2['failed']}"
)
print(
    f"  Refinery called {mock_r2.run.call_count} time(s)  (once per successful packet)"
)

print("\n  Normalised payloads written:")
for call in mock_l2.run.call_args_list:
    data = call.kwargs.get("input_data") or (call.args[0] if call.args else None)
    dest = call.kwargs.get("destination") or (
        call.args[1] if len(call.args) > 1 else "?"
    )
    import os

    if isinstance(data, list) and data:
        print(f"    → {os.path.basename(dest)}  text={data[0].content!r}")
```

## Refinery as Content Filter

Refinery returning [] silently drops the packet — no write, no error.

```python
FILTERED = [
    [MagicMock(content="Keep this.")],
    [],  # empty → packet skipped
    [MagicMock(content="Keep that.")],
]
filter_iter = iter(FILTERED)
three = [
    SayouPacket(data="important", success=True, meta={"filename": "f1.txt"}),
    SayouPacket(data="noise", success=True, meta={"filename": "f2.txt"}),
    SayouPacket(data="also keep", success=True, meta={"filename": "f3.txt"}),
]
mock_c3 = MagicMock()
mock_c3.run.return_value = iter(three)
mock_r3 = MagicMock()
mock_r3.run.side_effect = lambda data, **kw: next(filter_iter, [])
mock_l3 = MagicMock()
mock_l3.run.return_value = True

pipeline3 = TransferPipeline()
with patch.object(pipeline3, "connector", mock_c3), patch.object(
    pipeline3, "refinery", mock_r3
), patch.object(pipeline3, "loader", mock_l3):
    stats3 = pipeline3.ingest("src://x", destination="./out/", use_refinery=True)

print("\n=== Refinery as Content Filter ===")
print(f"  Input packets : 3")
print(f"  Written       : {stats3['written']}  (f2 filtered — Refinery returned [])")
print(f"  Failed        : {stats3['failed']}")
```

## Stats Summary

```python
print("\n=== Stats Summary ===")
print(f"  {'Scenario':22s}  read  written  failed")
print(f"  {'-'*45}")
for label, s in [
    ("No Refinery", stats),
    ("With Refinery", stats2),
    ("Filtered", stats3),
]:
    print(f"  {label:22s}  {s['read']:4d}  {s['written']:7d}  {s['failed']:6d}")
```