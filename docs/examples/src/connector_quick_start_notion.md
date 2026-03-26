!!! abstract "Source"
    Synced from [`packages/sayou-connector/examples/quick_start_notion.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-connector/examples/quick_start_notion.py).

## Setup

Collect Notion pages and archive them as Markdown files using
`TransferPipeline`.

`NotionGenerator` discovers pages accessible by an integration token.
`NotionFetcher` traverses each page's block tree and returns the content
as Markdown with full metadata.

Install the dependency before running with a real workspace:

```bash
pip install requests
python quick_start_notion.py
```

The example below mocks all HTTP calls so it runs without any credentials.
Remove `setup_mock()`, set the `NOTION_TOKEN` environment variable, and
point `source` at your workspace to go live.

**Create a Notion integration token:**
https://www.notion.so/my-integrations — then share target pages with the
integration.

```python
import json
import os
import sys
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline

OUTPUT_DIR = "./sayou_archive/notion"
```

## Mock Setup

`NotionGenerator` calls `requests.post` (search endpoint) to list pages.
`NotionFetcher` calls `requests.get` (page + blocks endpoints) to fetch
each page's block tree.

The mock returns two pages from search and a minimal block structure on
every fetch.  Patch `requests.get.return_value.json` to change the content.

To switch to live mode: delete this function and its call below.

```python
def setup_mock():
    mock_requests = MagicMock()

    # POST /v1/search — page list
    mock_requests.post.return_value.status_code = 200
    mock_requests.post.return_value.json.return_value = {
        "results": [
            {
                "id": "page-001",
                "properties": {
                    "title": {
                        "type": "title",
                        "title": [{"plain_text": "Project Overview"}],
                    }
                },
            },
            {
                "id": "page-002",
                "properties": {
                    "title": {
                        "type": "title",
                        "title": [{"plain_text": "Meeting Notes Q1"}],
                    }
                },
            },
        ]
    }

    # GET /v1/pages/{id} and /v1/blocks/{id}/children
    mock_requests.get.return_value.status_code = 200
    mock_requests.get.return_value.json.return_value = {
        "object": "page",
        "id": "page-001",
        "last_edited_time": "2024-01-15T10:00:00.000Z",
        "url": "https://notion.so/page-001",
        "properties": {
            "title": {
                "type": "title",
                "title": [{"plain_text": "Project Overview"}],
            }
        },
        "results": [
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "plain_text": "This project aims to build a next-generation data pipeline."
                        }
                    ]
                },
                "has_children": False,
            },
            {
                "type": "heading_2",
                "heading_2": {"rich_text": [{"plain_text": "Goals"}]},
                "has_children": False,
            },
        ],
        "has_more": False,
    }

    sys.modules["requests"] = mock_requests
```

## Collect All Accessible Pages

`notion://search` discovers all pages the integration token can access.
Each page becomes one Markdown file in `destination`.

`packet.data` contains:
- `content` — page body as Markdown
- `meta`    — title, url, last_edited_time, page_id

```python
setup_mock()

stats = TransferPipeline.process(
    source="notion://search",
    destination=OUTPUT_DIR,
    strategies={"connector": "notion"},
    notion_token=os.environ.get("NOTION_TOKEN", "mock-token"),
)

print("=== Collect All Accessible Pages ===")
print(json.dumps(stats, indent=2))
```

## Collect a Specific Page

Use `notion://page/{page_id}` to target a single page.
Copy the page ID from the Notion URL:
`https://www.notion.so/{workspace}/{page_id}`

```python
setup_mock()

stats_single = TransferPipeline.process(
    source="notion://page/page-001",
    destination=f"{OUTPUT_DIR}/single",
    strategies={"connector": "notion"},
    notion_token=os.environ.get("NOTION_TOKEN", "mock-token"),
)

print("=== Collect a Specific Page ===")
print(json.dumps(stats_single, indent=2))
```

## Validate Output

Inspect one of the archived files to confirm the Markdown content and
metadata were captured correctly.

```python
if os.path.isdir(OUTPUT_DIR):
    files = [
        n for n in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, n))
    ]
    print(f"\nArchived {len(files)} page(s) in '{OUTPUT_DIR}'.")
    if files:
        sample_path = os.path.join(OUTPUT_DIR, files[0])
        with open(sample_path, encoding="utf-8") as f:
            print(f.read(300))
```