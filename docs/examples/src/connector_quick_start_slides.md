!!! abstract "Source"
    Synced from [`packages/sayou-connector/examples/quick_start_slides.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-connector/examples/quick_start_slides.py).

## Setup

Collect Google Slides presentations and archive the extracted text using
`TransferPipeline`.

`GoogleDriveGenerator` discovers files in a Drive folder and routes
presentations (`application/vnd.google-apps.presentation`) to
`GoogleSlidesFetcher` via `source_type="slides"`.

`GoogleSlidesFetcher` uses the Slides API v1 to retrieve the full
presentation structure.  It iterates through every slide and extracts text
from shapes and tables, returning the raw `pageElements` list per slide.

`packet.data` is a nested list — one entry per slide, each containing the
raw `pageElements` from the Slides API.  Use the Chunking pipeline's `json`
strategy to further process the structure, or flatten it into plain text
for indexing.

Install the dependencies before running with a real account:

```bash
pip install google-api-python-client google-auth
python quick_start_google_slides.py
```

The example below mocks all Google API calls so it runs without any OAuth
token.  Remove `setup_mock()`, obtain a `token.json` with the
`drive.readonly` and `presentations.readonly` scopes, and set
`GOOGLE_TOKEN_PATH` to go live.

```python
import json
import os
import sys
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline

OUTPUT_DIR = "./sayou_archive/google_slides"
```

## Mock Setup

The mock simulates a Drive folder with two presentations.

`GoogleSlidesFetcher` calls:
  - `service.presentations().get(presentationId=…).execute()`

The mock returns a presentation with two slides:
  - Slide 1: a title text box
  - Slide 2: a text box and a two-column table

To switch to live mode: delete this function and its call below.

```python
def setup_mock():
    def _make_text_element(text: str) -> dict:
        return {"shape": {"text": {"textElements": [{"textRun": {"content": text}}]}}}

    def _make_table_element(rows: list) -> dict:
        return {
            "table": {
                "tableRows": [
                    {
                        "tableCells": [
                            {"text": {"textElements": [{"textRun": {"content": cell}}]}}
                            for cell in row
                        ]
                    }
                    for row in rows
                ]
            }
        }

    mock_presentation = {
        "title": "Q1 Engineering Review",
        "slides": [
            {
                "pageElements": [
                    _make_text_element("Q1 Engineering Review"),
                    _make_text_element("Presented by the Platform Team"),
                ]
            },
            {
                "pageElements": [
                    _make_text_element("Key Metrics"),
                    _make_table_element(
                        [
                            ["Metric", "Q1", "Target"],
                            ["Throughput", "1.2M", "1.0M"],
                            ["Error rate", "0.03%", "< 0.1%"],
                            ["P99 latency", "120ms", "< 200ms"],
                        ]
                    ),
                ]
            },
        ],
    }

    # --- Drive: file list ---
    mock_files_list = MagicMock()
    mock_files_list.list.return_value.execute.return_value = {
        "files": [
            {
                "id": "pres-001",
                "name": "Q1 Engineering Review",
                "mimeType": "application/vnd.google-apps.presentation",
                "webViewLink": "https://docs.google.com/presentation/d/pres-001",
                "createdTime": "2024-03-01T09:00:00Z",
                "modifiedTime": "2024-03-31T17:00:00Z",
            },
            {
                "id": "pres-002",
                "name": "Roadmap 2024 H2",
                "mimeType": "application/vnd.google-apps.presentation",
                "webViewLink": "https://docs.google.com/presentation/d/pres-002",
                "createdTime": "2024-04-01T09:00:00Z",
                "modifiedTime": "2024-04-15T11:00:00Z",
            },
        ]
    }

    mock_slides_service = MagicMock()
    mock_slides_service.presentations.return_value.get.return_value.execute.return_value = (
        mock_presentation
    )

    mock_drive_service = MagicMock()
    mock_drive_service.files.return_value = mock_files_list

    def _build(service_name, *args, **kwargs):
        if service_name == "drive":
            return mock_drive_service
        return mock_slides_service

    mock_creds = MagicMock()
    mock_creds_module = MagicMock()
    mock_creds_module.Credentials.from_authorized_user_file.return_value = mock_creds

    mock_discovery = MagicMock()
    mock_discovery.build.side_effect = _build

    sys.modules["googleapiclient"] = MagicMock()
    sys.modules["googleapiclient.discovery"] = mock_discovery
    sys.modules["googleapiclient.http"] = MagicMock()
    sys.modules["googleapiclient.errors"] = MagicMock()
    sys.modules["google"] = MagicMock()
    sys.modules["google.oauth2"] = MagicMock()
    sys.modules["google.oauth2.credentials"] = mock_creds_module
    sys.modules["chardet"] = MagicMock()
```

## Collect Presentations from a Folder

Point `source` at any Drive folder.  `GoogleDriveGenerator` auto-routes
presentation files to `GoogleSlidesFetcher`.

`packet.data` is a list of `pageElements` lists (one entry per slide),
as returned by the Slides API v1.  This preserves the full structural
information — text boxes, tables, images, shapes — for downstream use.

Each presentation is written as a single archive file in `destination`.

```python
setup_mock()

stats = TransferPipeline.process(
    source="gdrive://root",
    destination=OUTPUT_DIR,
    strategies={"connector": "drive"},
    google_token_path=os.environ.get("GOOGLE_TOKEN_PATH", "./token.json"),
)

print("=== Collect Presentations from a Folder ===")
print(json.dumps(stats, indent=2))
```

## Collect from a Specific Slides Folder

Use a dedicated Drive folder that contains only presentations to scope
the collection precisely.

```python
FOLDER_ID = os.environ.get("GDRIVE_SLIDES_FOLDER_ID", "my-slides-folder-id")

setup_mock()

stats_folder = TransferPipeline.process(
    source=f"gdrive://{FOLDER_ID}",
    destination=f"{OUTPUT_DIR}/decks",
    strategies={"connector": "drive"},
    google_token_path=os.environ.get("GOOGLE_TOKEN_PATH", "./token.json"),
)

print("=== Collect from a Specific Slides Folder ===")
print(json.dumps(stats_folder, indent=2))
```

## Validate Output

Each presentation produces one archive file.  The raw `pageElements`
structure is preserved — use the `json` chunking strategy to split by
slide, or flatten the text elements for full-text indexing.

```python
if os.path.isdir(OUTPUT_DIR):
    files = [
        n for n in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, n))
    ]
    print(f"\nArchived {len(files)} presentation(s) in '{OUTPUT_DIR}'.")
    if files:
        with open(os.path.join(OUTPUT_DIR, files[0]), encoding="utf-8") as f:
            print(f.read(400))
```