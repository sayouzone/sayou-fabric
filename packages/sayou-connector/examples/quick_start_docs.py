# ── Setup
"""
Collect Google Docs documents and archive them using `TransferPipeline`.

`GoogleDriveGenerator` lists files in a Drive folder and filters by MIME
type.  When it encounters a Google Docs file
(`application/vnd.google-apps.document`) it yields a task with URI
`gdocs://document/{file_id}` and `source_type="docs"`.

`GoogleDocsFetcher` then fetches the document using one of two modes:

| `fetch_mode` | API used        | Output format | Best for           |
|--------------|-----------------|---------------|--------------------|
| `"html"`     | Drive export    | HTML string   | Downstream parsing |
| `"json"`     | Docs API v1     | Raw API dict  | Structured access  |

The HTML export mode bypasses the 10 MB export limit that affects the
standard Drive download endpoint.

Install the dependencies before running with a real account:

```bash
pip install google-api-python-client google-auth
python quick_start_google_docs.py
```

The example below mocks all Google API calls so it runs without any OAuth
token.  Remove `setup_mock()`, obtain a `token.json` with the
`drive.readonly` and `documents.readonly` scopes, and set
`GOOGLE_TOKEN_PATH` to go live.
"""
import json
import os
import sys
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline

OUTPUT_DIR = "./sayou_archive/google_docs"


# ── Mock Setup
"""
The mock simulates a Drive folder that contains two Google Docs files and
one PDF (which is excluded by the Docs fetcher's URI filter).

`GoogleDriveGenerator` calls `service.files().list().execute()` and yields
tasks only for `application/vnd.google-apps.document` MIME types.

`GoogleDocsFetcher` (HTML mode) calls:
  - `service.files().export_media(fileId=…, mimeType="text/html")`
  - `MediaIoBaseDownload` to stream the response

To switch to live mode: delete this function and its call below.
"""


def setup_mock():
    import io

    # --- Drive: file list ---
    mock_files_list = MagicMock()
    mock_files_list.list.return_value.execute.return_value = {
        "files": [
            {
                "id": "doc-001",
                "name": "Engineering Spec v2",
                "mimeType": "application/vnd.google-apps.document",
                "webViewLink": "https://docs.google.com/document/d/doc-001",
                "createdTime": "2024-01-10T09:00:00Z",
                "modifiedTime": "2024-03-01T14:00:00Z",
            },
            {
                "id": "doc-002",
                "name": "Product Roadmap 2024",
                "mimeType": "application/vnd.google-apps.document",
                "webViewLink": "https://docs.google.com/document/d/doc-002",
                "createdTime": "2024-02-01T09:00:00Z",
                "modifiedTime": "2024-02-20T11:00:00Z",
            },
            {
                # PDF files are fetched by GoogleDriveFetcher, not GoogleDocsFetcher
                "id": "pdf-003",
                "name": "Architecture.pdf",
                "mimeType": "application/pdf",
                "webViewLink": "https://drive.google.com/file/d/pdf-003",
                "createdTime": "2024-01-05T00:00:00Z",
                "modifiedTime": "2024-01-05T00:00:00Z",
            },
        ]
    }

    # --- Drive: HTML export ---
    html_content = b"""<html><body>
<h1>Engineering Spec v2</h1>
<h2>Overview</h2>
<p>This document describes the chunking pipeline architecture.</p>
<h2>Requirements</h2>
<ul><li>Python 3.9+</li><li>Pydantic v2</li></ul>
</body></html>"""

    mock_downloader_instance = MagicMock()
    mock_downloader_instance.next_chunk.side_effect = [
        (MagicMock(progress=lambda: 1.0), True),
    ]

    def _fake_next_chunk():
        html_content_io = io.BytesIO(html_content)
        return (MagicMock(), True)

    # MediaIoBaseDownload writes into the fh buffer
    def _fake_download_init(fh, request):
        dl = MagicMock()

        def _next_chunk():
            fh.write(html_content)
            return (MagicMock(), True)

        dl.next_chunk.side_effect = _next_chunk
        return dl

    mock_drive_service = MagicMock()
    mock_drive_service.files.return_value = mock_files_list

    mock_creds = MagicMock()
    mock_creds_module = MagicMock()
    mock_creds_module.Credentials.from_authorized_user_file.return_value = mock_creds

    mock_discovery = MagicMock()
    mock_discovery.build.return_value = mock_drive_service

    mock_media_http = MagicMock()
    mock_media_http.MediaIoBaseDownload.side_effect = _fake_download_init

    sys.modules["googleapiclient"] = MagicMock()
    sys.modules["googleapiclient.discovery"] = mock_discovery
    sys.modules["googleapiclient.http"] = mock_media_http
    sys.modules["googleapiclient.errors"] = MagicMock()
    sys.modules["google"] = MagicMock()
    sys.modules["google.oauth2"] = MagicMock()
    sys.modules["google.oauth2.credentials"] = mock_creds_module
    sys.modules["chardet"] = MagicMock()


# ── Collect Docs from a Folder (HTML mode)
"""
Point `source` at any Drive folder.  `GoogleDriveGenerator` auto-routes
Google Docs files to `GoogleDocsFetcher`.

`fetch_mode="html"` (default) exports each document as a formatted HTML
string — ideal for downstream Refinery or chunking.

Each document is written as an HTML file in `destination`.
"""
setup_mock()

stats = TransferPipeline.process(
    source="gdrive://root",
    destination=OUTPUT_DIR,
    strategies={"connector": "drive"},
    google_token_path=os.environ.get("GOOGLE_TOKEN_PATH", "./token.json"),
    fetch_mode="html",
)

print("=== Collect Docs (HTML mode) ===")
print(json.dumps(stats, indent=2))


# ── Collect Docs from a Specific Folder (JSON mode)
"""
`fetch_mode="json"` fetches the raw Docs API v1 response — a structured
dict that includes paragraph styles, named ranges, inline objects, and tab
information.  Use this mode when you need precise structural control.
"""
FOLDER_ID = os.environ.get("GDRIVE_DOCS_FOLDER_ID", "my-docs-folder-id")

setup_mock()

stats_json = TransferPipeline.process(
    source=f"gdrive://{FOLDER_ID}",
    destination=f"{OUTPUT_DIR}/json_mode",
    strategies={"connector": "drive"},
    google_token_path=os.environ.get("GOOGLE_TOKEN_PATH", "./token.json"),
    fetch_mode="json",
)

print("=== Collect Docs (JSON mode) ===")
print(json.dumps(stats_json, indent=2))


# ── Validate Output
"""
Each document produces one file.  HTML mode writes `.html`; JSON mode
writes the raw API dict.  Inspect a sample to confirm the content and
metadata were captured correctly.
"""
if os.path.isdir(OUTPUT_DIR):
    files = [
        n for n in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, n))
    ]
    print(f"\nArchived {len(files)} document(s) in '{OUTPUT_DIR}'.")
    if files:
        with open(os.path.join(OUTPUT_DIR, files[0]), encoding="utf-8") as f:
            print(f.read(400))
