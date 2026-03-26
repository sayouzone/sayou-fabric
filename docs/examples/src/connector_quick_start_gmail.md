!!! abstract "Source"
    Synced from [`packages/sayou-connector/examples/quick_start_gmail.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-connector/examples/quick_start_gmail.py).

## Setup

Collect Gmail messages and archive them as HTML files using
`TransferPipeline`.

`GmailGenerator` lists message IDs from the inbox (or any Gmail search
query).  `GmailFetcher` downloads each message's full payload, parses the
MIME structure, and returns a self-contained HTML document with embedded
metadata headers.

Install the dependencies before running with a real account:

```bash
pip install google-api-python-client google-auth
python quick_start_gmail.py
```

The example below mocks all Gmail API calls so it runs without any OAuth
token.  Remove `setup_mock()`, generate a `token.json` via the Google
OAuth flow (with `gmail.readonly` scope), and set `GOOGLE_TOKEN_PATH`.

```python
import json
import os
import sys
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline

OUTPUT_DIR = "./sayou_archive/gmail"
```

## Mock Setup

`GmailGenerator` calls:
  - `service.users().messages().list(userId="me", q=…)` — list message IDs

`GmailFetcher` calls:
  - `service.users().messages().get(userId="me", id=…, format="full")` — full payload

The mock simulates an inbox with two messages, one plain-text and one HTML.
The body is base64url-encoded as the Gmail API returns it.

To switch to live mode: delete this function and its call below.

```python
def setup_mock():
    import base64

    def _encode(text: str) -> str:
        return base64.urlsafe_b64encode(text.encode()).decode()

    mock_service = MagicMock()

    # List messages
    mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
        "messages": [
            {"id": "msg-001", "threadId": "thread-001"},
            {"id": "msg-002", "threadId": "thread-002"},
        ]
    }

    # Full message payload (alternating by call count via side_effect)
    msg_001 = {
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "Subject", "value": "Weekly Digest: AI Highlights"},
                {"name": "From", "value": "newsletter@example.com"},
                {"name": "Date", "value": "Mon, 01 Apr 2024 09:00:00 +0000"},
            ],
            "body": {"data": _encode("<p>Top stories this week in AI.</p>")},
        }
    }
    msg_002 = {
        "payload": {
            "mimeType": "text/html",
            "headers": [
                {"name": "Subject", "value": "Your order has shipped"},
                {"name": "From", "value": "orders@shop.example.com"},
                {"name": "Date", "value": "Tue, 02 Apr 2024 14:00:00 +0000"},
            ],
            "body": {
                "data": _encode(
                    "<h1>Order Shipped!</h1><p>Your package is on its way.</p>"
                )
            },
        }
    }

    mock_service.users.return_value.messages.return_value.get.return_value.execute.side_effect = [
        msg_001,
        msg_002,
    ]

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

## Collect Inbox

`source` format: `gmail://me` (always `me` — refers to the authenticated user).

The `query` keyword accepts any Gmail search expression:
  - `"is:inbox"`             — inbox messages (default)
  - `"is:unread"`            — unread only
  - `"from:newsletter@…"`   — filter by sender
  - `"subject:digest"`       — filter by subject
  - `"after:2024/01/01"`     — messages after a date

`limit` caps the number of messages fetched (default: 10).

Each message is archived as an HTML file named after the message ID.

```python
setup_mock()

stats = TransferPipeline.process(
    source="gmail://me",
    destination=OUTPUT_DIR,
    strategies={"connector": "gmail"},
    token_path=os.environ.get("GOOGLE_TOKEN_PATH", "./token.json"),
    query="is:inbox",
    limit=10,
)

print("=== Collect Inbox ===")
print(json.dumps(stats, indent=2))
```

## Collect with Search Filter

Use Gmail search syntax to target specific messages.
This example collects unread newsletters from the last 7 days.

```python
setup_mock()

stats_filtered = TransferPipeline.process(
    source="gmail://me",
    destination=f"{OUTPUT_DIR}/newsletters",
    strategies={"connector": "gmail"},
    token_path=os.environ.get("GOOGLE_TOKEN_PATH", "./token.json"),
    query="is:unread category:promotions newer_than:7d",
    limit=20,
)

print("=== Collect with Search Filter ===")
print(json.dumps(stats_filtered, indent=2))
```

## Validate Output

Each message produces one HTML file.  Open one to confirm the subject,
sender, date, and body were extracted and embedded correctly.

```python
if os.path.isdir(OUTPUT_DIR):
    files = [
        n for n in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, n))
    ]
    print(f"\nArchived {len(files)} message(s) in '{OUTPUT_DIR}'.")
    if files:
        with open(os.path.join(OUTPUT_DIR, files[0]), encoding="utf-8") as f:
            print(f.read(400))
```