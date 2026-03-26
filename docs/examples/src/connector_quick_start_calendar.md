!!! abstract "Source"
    Synced from [`packages/sayou-connector/examples/quick_start_calendar.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-connector/examples/quick_start_calendar.py).

## Setup

Collect Google Calendar events and archive them using `TransferPipeline`.

`GoogleCalendarGenerator` yields a single task per calendar.
`GoogleCalendarFetcher` retrieves events in a ±30-day window via the
Google Calendar API v3 and returns a list of structured event dicts.

Install the dependencies before running with a real account:

```bash
pip install google-api-python-client google-auth
python quick_start_google_calendar.py
```

The example below mocks all Google API calls so it runs without any OAuth
token.  Remove `setup_mock()`, obtain a `token.json` via the standard
Google OAuth flow, and set `GOOGLE_TOKEN_PATH` to go live.

```python
import json
import os
import sys
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline

OUTPUT_DIR = "./sayou_archive/google_calendar"
```

## Mock Setup

`GoogleCalendarFetcher` calls `googleapiclient.discovery.build("calendar", "v3")`
then `service.events().list(...).execute()`.

The mock returns two calendar events — one all-day event and one timed
meeting with attendees.

To switch to live mode: delete this function and its call below.

```python
def setup_mock():
    mock_events = MagicMock()
    mock_events.list.return_value.execute.return_value = {
        "items": [
            {
                "id": "event-001",
                "summary": "Q2 Planning Meeting",
                "description": "Quarterly planning session with all leads.",
                "start": {"dateTime": "2024-04-01T10:00:00+09:00"},
                "end": {"dateTime": "2024-04-01T11:30:00+09:00"},
                "location": "Conference Room A",
                "htmlLink": "https://calendar.google.com/event?eid=event-001",
                "attendees": [
                    {"email": "alice@example.com", "responseStatus": "accepted"},
                    {"email": "bob@example.com", "responseStatus": "tentative"},
                ],
            },
            {
                "id": "event-002",
                "summary": "Public Holiday",
                "description": "",
                "start": {"date": "2024-04-10"},
                "end": {"date": "2024-04-11"},
                "location": "",
                "htmlLink": "https://calendar.google.com/event?eid=event-002",
                "attendees": [],
            },
        ]
    }

    mock_service = MagicMock()
    mock_service.events.return_value = mock_events

    mock_creds = MagicMock()
    mock_creds_module = MagicMock()
    mock_creds_module.Credentials.from_authorized_user_file.return_value = mock_creds

    mock_discovery = MagicMock()
    mock_discovery.build.return_value = mock_service

    sys.modules["googleapiclient"] = MagicMock()
    sys.modules["googleapiclient.discovery"] = mock_discovery
    sys.modules["google"] = MagicMock()
    sys.modules["google.oauth2"] = MagicMock()
    sys.modules["google.oauth2.credentials"] = mock_creds_module
```

## Collect Primary Calendar

`source` format: `gcal://{calendar_id}`

Use `gcal://primary` for your main calendar.  For a shared or secondary
calendar, replace `primary` with the calendar's email address.

`packet.data["content"]` is a list of event dicts, each containing:
`id`, `summary`, `description`, `start`, `end`, `location`, `htmlLink`,
and `attendees`.

```python
setup_mock()

stats = TransferPipeline.process(
    source="gcal://primary",
    destination=OUTPUT_DIR,
    strategies={"connector": "google_calendar"},
    google_token_path=os.environ.get("GOOGLE_TOKEN_PATH", "./token.json"),
)

print("=== Collect Primary Calendar ===")
print(json.dumps(stats, indent=2))
```

## Collect a Shared Calendar

Pass any calendar ID after `gcal://` to target a specific calendar.
Calendar IDs look like email addresses (e.g. `team@group.calendar.google.com`).

```python
setup_mock()

stats_shared = TransferPipeline.process(
    source="gcal://team@group.calendar.google.com",
    destination=f"{OUTPUT_DIR}/team",
    strategies={"connector": "google_calendar"},
    google_token_path=os.environ.get("GOOGLE_TOKEN_PATH", "./token.json"),
)

print("=== Collect a Shared Calendar ===")
print(json.dumps(stats_shared, indent=2))
```

## Validate Output

Each calendar archive is a JSON file containing the event list.
Inspect the file to confirm that all event fields were captured.

```python
if os.path.isdir(OUTPUT_DIR):
    files = [
        n for n in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, n))
    ]
    print(f"\nArchived {len(files)} calendar file(s) in '{OUTPUT_DIR}'.")
    if files:
        with open(os.path.join(OUTPUT_DIR, files[0]), encoding="utf-8") as f:
            print(f.read(400))
```