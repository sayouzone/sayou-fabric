# ── Setup
"""
Transfer files from the local file system to an archive directory.

`FileGenerator` walks a directory tree and yields one task per matching
file.  `FileFetcher` reads each file as raw bytes.  No external
dependencies or credentials are required.

```bash
mkdir -p ./sample_data && echo "Hello Sayou" > ./sample_data/readme.txt
python quick_start_file.py
```
"""
import json
import os

from sayou.brain.pipelines.transfer import TransferPipeline

OUTPUT_DIR = "./sayou_archive/file"


# ── Collect a Directory
"""
Pass any local directory path as `source`.  Use the `extensions` keyword to
restrict which file types are collected.

`TransferPipeline.process()` returns:
```python
{"read": <int>, "written": <int>, "failed": <int>}
```
"""
stats = TransferPipeline.process(
    source="./sample_data",
    destination=OUTPUT_DIR,
    strategies={"connector": "file"},
    extensions=[".txt", ".md", ".pdf"],
)

print("=== Collect a Directory ===")
print(json.dumps(stats, indent=2))


# ── Filter by Glob Pattern
"""
`name_pattern` is an `fnmatch`-style glob applied on top of the extension
filter.  Only files whose basename matches the pattern are transferred.
"""
stats_glob = TransferPipeline.process(
    source="./sample_data",
    destination=os.path.join(OUTPUT_DIR, "reports"),
    strategies={"connector": "file"},
    extensions=[".txt"],
    name_pattern="report_*",
)

print("=== Filter by Glob Pattern ===")
print(json.dumps(stats_glob, indent=2))


# ── Non-recursive Scan
"""
Set `recursive=False` to collect only the top-level directory without
descending into sub-directories.
"""
stats_flat = TransferPipeline.process(
    source="./sample_data",
    destination=os.path.join(OUTPUT_DIR, "flat"),
    strategies={"connector": "file"},
    extensions=[".txt"],
    recursive=False,
)

print("=== Non-recursive Scan ===")
print(json.dumps(stats_flat, indent=2))


# ── Validate Output
"""
After a successful transfer each collected file appears in `destination`.
Inspect the directory to confirm the transfer completed cleanly.
"""
if os.path.isdir(OUTPUT_DIR):
    names = [
        n for n in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, n))
    ]
    print(f"\nArchived {len(names)} file(s) in '{OUTPUT_DIR}'.")
    for name in names[:5]:
        size = os.path.getsize(os.path.join(OUTPUT_DIR, name))
        print(f"  {name}  ({size} bytes)")
