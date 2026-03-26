!!! abstract "Source"
    Synced from [`packages/sayou-connector/examples/quick_start_trafilatura.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-connector/examples/quick_start_trafilatura.py).

## Setup

Extract and archive the main article content from any web page using
`TrafilaturaFetcher`.

`trafilatura` downloads the raw HTML and strips ads, navigation bars, and
boilerplate, returning the article body as clean Markdown.

Install the dependency before running with a real URL:

```bash
pip install trafilatura
python quick_start_trafilatura.py
```

The example below uses a mock so it runs without an internet connection.
Remove `setup_mock()` and substitute a real URL to collect live content.

```python
import json
import sys
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline

OUTPUT_DIR = "./sayou_archive/trafilatura"
```

## Mock Setup

`TrafilaturaFetcher` calls `trafilatura.fetch_url()` then
`trafilatura.extract()`.  The mock below returns a fixed Markdown string
so the full pipeline path is exercised without a network connection.

To switch to live mode: delete this function and its call below.

```python
def setup_mock():
    mock = MagicMock()
    mock.fetch_url.return_value = "<html><body><p>Article body.</p></body></html>"
    mock.extract.return_value = (
        "# How Trafilatura Works\n\n"
        "Trafilatura downloads the raw HTML of a page and removes boilerplate "
        "content such as navigation menus, advertisements, and footers.\n\n"
        "The extracted Markdown is ready for downstream chunking or indexing."
    )
    sys.modules["trafilatura"] = mock
```

## Transfer a Single URL

Prefix the target URL with `trafilatura://` to route through
`TrafilaturaGenerator` and `TrafilaturaFetcher`.

`packet.data` is the extracted Markdown string.  `TransferPipeline` writes
it to a file under `destination`.

```python
setup_mock()

stats = TransferPipeline.process(
    source="trafilatura://https://example.com/article",
    destination=OUTPUT_DIR,
    strategies={"connector": "trafilatura"},
)

print("=== Transfer a Single URL ===")
print(json.dumps(stats, indent=2))
```

## Transfer Multiple URLs

Call `TransferPipeline.process()` once per URL.  All strategies are
stateless — multiple calls are safe and independent.

```python
urls = [
    "trafilatura://https://example.com/page-1",
    "trafilatura://https://example.com/page-2",
    "trafilatura://https://example.com/page-3",
]

total = {"read": 0, "written": 0, "failed": 0}
for url in urls:
    s = TransferPipeline.process(
        source=url,
        destination=f"{OUTPUT_DIR}/batch",
        strategies={"connector": "trafilatura"},
    )
    for k in total:
        total[k] += s.get(k, 0)

print("=== Transfer Multiple URLs ===")
print(json.dumps(total, indent=2))
```

## Validate Output

Each URL produces one file in `destination`.  Inspect the first file to
confirm that extraction produced readable content.

```python
import os

if os.path.isdir(OUTPUT_DIR):
    files = [
        n for n in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, n))
    ]
    print(f"\nArchived {len(files)} file(s) in '{OUTPUT_DIR}'.")
    if files:
        sample_path = os.path.join(OUTPUT_DIR, files[0])
        with open(sample_path, encoding="utf-8") as f:
            preview = f.read(200)
        print(f"Preview of '{files[0]}':\n{preview}")
```