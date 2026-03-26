!!! abstract "Source"
    Synced from [`packages/sayou-connector/examples/quick_start_sheets.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-connector/examples/quick_start_sheets.py).

## Setup

Collect Google Sheets spreadsheets and archive them as CSV using
`TransferPipeline`.

`GoogleDriveGenerator` discovers files in a Drive folder and routes
spreadsheets (`application/vnd.google-apps.spreadsheet`) to
`GoogleSheetsFetcher` via `source_type="sheets"`.

`GoogleSheetsFetcher` uses the Sheets API v4 to fetch every sheet (tab)
in the spreadsheet and converts each one to CSV in memory.  Unlike the
Drive export endpoint, the Sheets API has no file-size limit and returns
one CSV string per sheet tab.

`packet.data` is a `list[dict]` where each entry is
`{"Sheet Name": "<csv_string>"}`.

Install the dependencies before running with a real account:

```bash
pip install google-api-python-client google-auth
python quick_start_google_sheets.py
```

The example below mocks all Google API calls so it runs without any OAuth
token.  Remove `setup_mock()`, obtain a `token.json` with the
`drive.readonly` and `spreadsheets.readonly` scopes, and set
`GOOGLE_TOKEN_PATH` to go live.

```python
import json
import os
import sys
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline

OUTPUT_DIR = "./sayou_archive/google_sheets"
```

## Mock Setup

The mock simulates a Drive folder with two spreadsheets.

`GoogleSheetsFetcher` calls:
  1. `service.spreadsheets().get(spreadsheetId=…).execute()` — sheet list
  2. `service.spreadsheets().values().get(spreadsheetId=…, range=sheet_title).execute()`
     — cell values for each tab

The mock returns two tabs: "Q1 Data" and "Q2 Data", each with a header row
and two data rows.

To switch to live mode: delete this function and its call below.

```python
def setup_mock():
    # --- Drive: file list ---
    mock_files_list = MagicMock()
    mock_files_list.list.return_value.execute.return_value = {
        "files": [
            {
                "id": "sheet-001",
                "name": "Sales Report 2024",
                "mimeType": "application/vnd.google-apps.spreadsheet",
                "webViewLink": "https://docs.google.com/spreadsheets/d/sheet-001",
                "createdTime": "2024-01-01T00:00:00Z",
                "modifiedTime": "2024-04-01T12:00:00Z",
            },
            {
                "id": "sheet-002",
                "name": "Employee Directory",
                "mimeType": "application/vnd.google-apps.spreadsheet",
                "webViewLink": "https://docs.google.com/spreadsheets/d/sheet-002",
                "createdTime": "2024-02-01T00:00:00Z",
                "modifiedTime": "2024-03-15T09:00:00Z",
            },
        ]
    }

    # --- Sheets API: spreadsheet metadata ---
    mock_spreadsheet_meta = {
        "properties": {"title": "Sales Report 2024"},
        "sheets": [
            {"properties": {"title": "Q1 Data"}},
            {"properties": {"title": "Q2 Data"}},
        ],
    }

    # --- Sheets API: cell values per tab ---
    q1_values = {
        "values": [
            ["Product", "Revenue", "Units"],
            ["Widget A", "12000", "240"],
            ["Widget B", "8500", "170"],
        ]
    }
    q2_values = {
        "values": [
            ["Product", "Revenue", "Units"],
            ["Widget A", "15000", "300"],
            ["Widget B", "11000", "220"],
        ]
    }

    mock_sheets_service = MagicMock()
    mock_sheets_service.spreadsheets.return_value.get.return_value.execute.return_value = (
        mock_spreadsheet_meta
    )
    mock_sheets_service.spreadsheets.return_value.values.return_value.get.return_value.execute.side_effect = [
        q1_values,
        q2_values,
        q1_values,
        q2_values,  # second spreadsheet call
    ]

    # Both drive and sheets share the mocked service via build()
    mock_drive_service = MagicMock()
    mock_drive_service.files.return_value = mock_files_list

    call_count = [0]

    def _build(service_name, *args, **kwargs):
        call_count[0] += 1
        if service_name == "drive":
            return mock_drive_service
        return mock_sheets_service

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

## Collect Spreadsheets from a Folder

Point `source` at any Drive folder.  `GoogleDriveGenerator` auto-routes
spreadsheet files to `GoogleSheetsFetcher`.

`packet.data` is a `list[dict]`:
```python
[
    {"Q1 Data": "Product,Revenue,Units\\nWidget A,12000,240\\n…"},
    {"Q2 Data": "Product,Revenue,Units\\nWidget A,15000,300\\n…"},
]
```

Each spreadsheet (all its tabs combined) is written as a single archive
file in `destination`.

```python
setup_mock()

stats = TransferPipeline.process(
    source="gdrive://root",
    destination=OUTPUT_DIR,
    strategies={"connector": "drive"},
    google_token_path=os.environ.get("GOOGLE_TOKEN_PATH", "./token.json"),
)

print("=== Collect Spreadsheets from a Folder ===")
print(json.dumps(stats, indent=2))
```

## Collect from a Specific Sheets Folder

Use a dedicated Drive folder that contains only spreadsheets to avoid
processing Docs or Slides files in the same run.

```python
FOLDER_ID = os.environ.get("GDRIVE_SHEETS_FOLDER_ID", "my-sheets-folder-id")

setup_mock()

stats_folder = TransferPipeline.process(
    source=f"gdrive://{FOLDER_ID}",
    destination=f"{OUTPUT_DIR}/reports",
    strategies={"connector": "drive"},
    google_token_path=os.environ.get("GOOGLE_TOKEN_PATH", "./token.json"),
)

print("=== Collect from a Specific Sheets Folder ===")
print(json.dumps(stats_folder, indent=2))
```

## Validate Output

Each spreadsheet produces one archive file containing the CSV data from
all tabs.  Inspect a sample to confirm that column headers and values
were captured correctly.

```python
if os.path.isdir(OUTPUT_DIR):
    files = [
        n for n in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, n))
    ]
    print(f"\nArchived {len(files)} spreadsheet(s) in '{OUTPUT_DIR}'.")
    if files:
        with open(os.path.join(OUTPUT_DIR, files[0]), encoding="utf-8") as f:
            print(f.read(400))
```