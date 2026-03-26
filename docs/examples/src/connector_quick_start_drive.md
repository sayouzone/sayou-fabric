!!! abstract "Source"
    Synced from [`packages/sayou-connector/examples/quick_start_drive.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-connector/examples/quick_start_drive.py).

## Setup

Collect files from Google Drive and archive them using `TransferPipeline`.

`GoogleDriveGenerator` lists files in a Drive folder via the Drive API v3.
`GoogleDriveFetcher` exports Google Workspace files (Docs → plain text,
Sheets → CSV, Slides → plain text) and downloads binary files as-is.

Install the dependencies before running with a real account:

```bash
pip install google-api-python-client google-auth
python quick_start_gdrive.py
```

The example below mocks all Google API calls so it runs without any OAuth
token.  Remove `setup_mock()`, obtain a token file via the standard Google
OAuth flow, and set `GOOGLE_TOKEN_PATH` to go live.

**Generate a token file:**
Follow the Google API Python Quickstart guide and run the auth script.
The resulting `token.json` is passed as `google_token_path`.

```python
import json
import os
import sys
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline

OUTPUT_DIR = "./sayou_archive/gdrive"
```

## Mock Setup

`GoogleDriveGenerator` calls `googleapiclient.discovery.build()` then
`service.files().list().execute()`.

`GoogleDriveFetcher` calls:
  - `service.files().export_media()` for Google Workspace files (Docs, Sheets)
  - `service.files().get_media()` for binary files (PDF, images)

The mock simulates a folder containing one Google Doc and one PDF.

To switch to live mode: delete this function and its call below.

```python
def setup_mock():
    mock_files = MagicMock()
    mock_files.list.return_value.execute.return_value = {
        "files": [
            {
                "id": "doc-001",
                "name": "Q1 Engineering Report",
                "mimeType": "application/vnd.google-apps.document",
                "webViewLink": "https://docs.google.com/document/d/doc-001",
                "createdTime": "2024-01-01T00:00:00Z",
                "modifiedTime": "2024-01-15T12:00:00Z",
            },
            {
                "id": "file-002",
                "name": "Architecture Diagram.pdf",
                "mimeType": "application/pdf",
                "webViewLink": "https://drive.google.com/file/d/file-002",
                "createdTime": "2024-01-05T00:00:00Z",
                "modifiedTime": "2024-01-05T00:00:00Z",
            },
        ]
    }
    mock_files.export_media.return_value.execute.return_value = (
        b"Q1 Engineering Report\n\nThis document summarises Q1 outcomes."
    )
    mock_files.get_media.return_value.execute.return_value = (
        b"%PDF-1.4 mock pdf content"
    )

    mock_service = MagicMock()
    mock_service.files.return_value = mock_files

    mock_creds = MagicMock()
    mock_creds_module = MagicMock()
    mock_creds_module.Credentials.from_authorized_user_file.return_value = mock_creds

    mock_discovery = MagicMock()
    mock_discovery.build.return_value = mock_service

    sys.modules["googleapiclient"] = MagicMock()
    sys.modules["googleapiclient.discovery"] = mock_discovery
    sys.modules["googleapiclient.http"] = MagicMock()
    sys.modules["google"] = MagicMock()
    sys.modules["google.oauth2"] = MagicMock()
    sys.modules["google.oauth2.credentials"] = mock_creds_module
```

## Collect My Drive Root

`source` format:
  - `gdrive://root`         — My Drive root
  - `gdrive://{folder_id}`  — specific folder

The folder ID appears in the Drive URL:
`https://drive.google.com/drive/folders/{FOLDER_ID}`

Each file is written to `destination`.  Google Workspace files are exported
as plain text; other files retain their original format.

```python
setup_mock()

stats = TransferPipeline.process(
    source="gdrive://root",
    destination=OUTPUT_DIR,
    strategies={"connector": "drive"},
    google_token_path=os.environ.get("GOOGLE_TOKEN_PATH", "./token.json"),
)

print("=== Collect My Drive Root ===")
print(json.dumps(stats, indent=2))
```

## Collect a Specific Folder

Copy the folder ID from the Drive URL and pass it after `gdrive://`.

```python
FOLDER_ID = os.environ.get("GDRIVE_FOLDER_ID", "mock-folder-id")

setup_mock()

stats_folder = TransferPipeline.process(
    source=f"gdrive://{FOLDER_ID}",
    destination=f"{OUTPUT_DIR}/folder",
    strategies={"connector": "drive"},
    google_token_path=os.environ.get("GOOGLE_TOKEN_PATH", "./token.json"),
)

print("=== Collect a Specific Folder ===")
print(json.dumps(stats_folder, indent=2))
```

## Validate Output

Inspect the archive to confirm that both Workspace exports and binary files
were written correctly.

```python
if os.path.isdir(OUTPUT_DIR):
    files = [
        n for n in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, n))
    ]
    print(f"\nArchived {len(files)} file(s) in '{OUTPUT_DIR}'.")
    for name in files[:5]:
        size = os.path.getsize(os.path.join(OUTPUT_DIR, name))
        print(f"  {name}  ({size} bytes)")
```