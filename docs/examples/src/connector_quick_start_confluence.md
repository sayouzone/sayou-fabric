!!! abstract "Source"
    Synced from [`packages/sayou-connector/examples/quick_start_confluence.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-connector/examples/quick_start_confluence.py).

## Setup

Collect Confluence pages and archive them as HTML files using
`TransferPipeline`.

`ConfluenceGenerator` lists pages from a space using CQL (Confluence Query
Language).  `ConfluenceFetcher` retrieves the full page body and wraps it
in a self-contained HTML document.

Install the dependency before running with a real instance:

```bash
pip install atlassian-python-api
python quick_start_confluence.py
```

The example below mocks all API calls so it runs without any credentials.
Remove `setup_mock()`, set the environment variables below, and point
`source` at your space key to go live.

**Create an Atlassian API token:**
https://id.atlassian.com/manage-profile/security/api-tokens

```python
import json
import os
import sys
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline

OUTPUT_DIR = "./sayou_archive/confluence"
```

## Mock Setup

`ConfluenceGenerator` calls `Confluence.cql()` to list pages.
`ConfluenceFetcher` calls `Confluence.get_page_by_id()` to fetch content.

The mock simulates a space with two pages.  Patch `cql.return_value` to
simulate different result sets.

To switch to live mode: delete this function and its call below.

```python
def setup_mock():
    mock_instance = MagicMock()

    mock_instance.cql.return_value = {
        "results": [
            {"id": "111001", "title": "Engineering Onboarding"},
            {"id": "111002", "title": "API Design Guidelines"},
        ]
    }

    mock_instance.get_page_by_id.return_value = {
        "title": "Engineering Onboarding",
        "body": {
            "storage": {
                "value": (
                    "<h2>Welcome</h2>"
                    "<p>This guide covers everything you need to get started "
                    "on the Engineering team.</p>"
                    "<h2>Setup</h2>"
                    "<p>Clone the monorepo and follow the README.</p>"
                )
            }
        },
        "_links": {
            "base": "https://acme.atlassian.net",
            "webui": "/wiki/spaces/ENG/pages/111001",
        },
        "version": {"number": 4, "when": "2024-02-01T09:00:00.000Z"},
    }

    mock_atlassian = MagicMock()
    mock_atlassian.Confluence.return_value = mock_instance
    sys.modules["atlassian"] = mock_atlassian
```

## Collect a Space

`source` format: `confluence://{SPACE_KEY}`

Leave the key empty (`confluence://`) to scan all spaces — use with
caution on large instances.

Each page is written as a self-contained HTML file in `destination`.

```python
setup_mock()

stats = TransferPipeline.process(
    source="confluence://ENG",
    destination=OUTPUT_DIR,
    strategies={"connector": "confluence"},
    url=os.environ.get("CONFLUENCE_URL", "https://mock.atlassian.net"),
    username=os.environ.get("CONFLUENCE_USERNAME", "user@example.com"),
    token=os.environ.get("CONFLUENCE_TOKEN", "mock-token"),
    limit=10,
)

print("=== Collect a Space ===")
print(json.dumps(stats, indent=2))
```

## Collect Multiple Spaces

Run the pipeline once per space key.  Each space writes to its own
sub-directory to keep the archives organised.

```python
spaces = ["confluence://ENG", "confluence://PRODUCT", "confluence://HR"]

total = {"read": 0, "written": 0, "failed": 0}
for space in spaces:
    setup_mock()
    key = space.replace("confluence://", "").lower()
    s = TransferPipeline.process(
        source=space,
        destination=f"{OUTPUT_DIR}/{key}",
        strategies={"connector": "confluence"},
        url=os.environ.get("CONFLUENCE_URL", "https://mock.atlassian.net"),
        username=os.environ.get("CONFLUENCE_USERNAME", "user@example.com"),
        token=os.environ.get("CONFLUENCE_TOKEN", "mock-token"),
        limit=5,
    )
    for k in total:
        total[k] += s.get(k, 0)

print("=== Collect Multiple Spaces ===")
print(json.dumps(total, indent=2))
```

## Validate Output

Each page produces one HTML file.  Open one to confirm that the title,
body, and metadata link were captured correctly.

```python
if os.path.isdir(OUTPUT_DIR):
    files = [
        n for n in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, n))
    ]
    print(f"\nArchived {len(files)} page(s) in '{OUTPUT_DIR}'.")
    if files:
        sample_path = os.path.join(OUTPUT_DIR, files[0])
        with open(sample_path, encoding="utf-8") as f:
            print(f.read(400))
```