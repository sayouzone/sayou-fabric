!!! abstract "Source"
    Synced from [`packages/sayou-connector/examples/quick_start_imap.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-connector/examples/quick_start_imap.py).

## Setup

Collect emails from any IMAP server and archive them as HTML files using
`TransferPipeline`.

`ImapEmailGenerator` connects via SSL, searches the inbox (or any folder),
and yields one task per email.  `ImapEmailFetcher` fetches each message by
UID, parses the MIME structure, and returns a self-contained HTML document.

Supports Gmail, Naver Mail, Daum Mail, Outlook, and any IMAP-compatible
server.  No third-party packages required (uses Python's `imaplib`).

```bash
python quick_start_imap.py
```

The example below mocks `imaplib` so it runs without any credentials.
Remove `setup_mock()`, set the environment variables below, and update
`imap_server` to go live.

**Gmail App Password:**
Google Account → Security → 2-Step Verification → App Passwords.

```python
import json
import os
import sys
from unittest.mock import MagicMock, patch

from sayou.brain.pipelines.transfer import TransferPipeline

OUTPUT_DIR = "./sayou_archive/imap"
```

## Mock Setup

`ImapEmailGenerator` calls:
  - `imaplib.IMAP4_SSL(server)` → `.login()` → `.select()` → `.search()`

`ImapEmailFetcher` calls:
  - `imaplib.IMAP4_SSL(server)` → `.login()` → `.select()` → `.fetch(uid, "(RFC822)")`

The mock returns two email UIDs from search and a minimal RFC 822 message
on every fetch call.

To switch to live mode: delete this function and its call below.

```python
def setup_mock():
    import email as email_lib
    from email.mime.text import MIMEText

    def _make_raw_email(subject: str, sender: str, body: str) -> bytes:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["Date"] = "Mon, 01 Apr 2024 09:00:00 +0000"
        return msg.as_bytes()

    mock_mail = MagicMock()
    mock_mail.__enter__ = lambda s: s
    mock_mail.__exit__ = MagicMock(return_value=False)

    # search → two UIDs
    mock_mail.search.return_value = ("OK", [b"1 2"])

    # fetch → RFC 822 raw bytes
    raw_1 = _make_raw_email(
        "Weekly AI Digest", "news@example.com", "Top AI stories this week."
    )
    raw_2 = _make_raw_email(
        "Your invoice #1042", "billing@shop.com", "Please find your invoice attached."
    )
    mock_mail.fetch.side_effect = [
        ("OK", [(b"1 (RFC822 {512})", raw_1)]),
        ("OK", [(b"2 (RFC822 {640})", raw_2)]),
    ]
    mock_mail.login.return_value = ("OK", [b"Logged in"])
    mock_mail.select.return_value = ("OK", [b"2"])

    mock_imaplib = MagicMock()
    mock_imaplib.IMAP4_SSL.return_value = mock_mail
    sys.modules["imaplib"] = mock_imaplib
```

## Collect Inbox (Gmail)

`source` format: `imap://{server}` — e.g. `imap://imap.gmail.com`

All connection details are passed as keyword arguments:
  - `username` — your email address
  - `password` — App Password (Gmail) or account password
  - `imap_server` — overrides the server in `source` when both differ
  - `folder` — IMAP folder to scan (default: `"INBOX"`)
  - `limit` — max number of emails to collect (default: 10)
  - `search_criteria` — IMAP search expression (default: `"ALL"`)

Each message is archived as an HTML file containing the subject, sender,
date, and decoded body (HTML preferred; plain text as fallback).

```python
setup_mock()

stats = TransferPipeline.process(
    source="imap://",
    destination=OUTPUT_DIR,
    strategies={"connector": "imap"},
    imap_server="imap.gmail.com",
    username=os.environ.get("IMAP_USERNAME", "user@gmail.com"),
    password=os.environ.get("IMAP_PASSWORD", "mock-app-password"),
    folder="INBOX",
    limit=10,
    search_criteria="ALL",
)

print("=== Collect Inbox (Gmail) ===")
print(json.dumps(stats, indent=2))
```

## Collect Unread Messages (Naver Mail)

Change `imap_server` to collect from any compatible provider.
Use `search_criteria="(UNSEEN)"` to collect only unread messages.

```python
setup_mock()

stats_naver = TransferPipeline.process(
    source="imap://",
    destination=f"{OUTPUT_DIR}/naver",
    strategies={"connector": "imap"},
    imap_server="imap.naver.com",
    username=os.environ.get("NAVER_USERNAME", "user@naver.com"),
    password=os.environ.get("NAVER_PASSWORD", "mock-password"),
    folder="INBOX",
    limit=20,
    search_criteria="(UNSEEN)",
)

print("=== Collect Unread Messages (Naver Mail) ===")
print(json.dumps(stats_naver, indent=2))
```

## Validate Output

Each email produces one HTML file.  The file embeds the subject, sender,
date, and UID in `<meta>` tags for downstream parsing.

```python
if os.path.isdir(OUTPUT_DIR):
    files = [
        n for n in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, n))
    ]
    print(f"\nArchived {len(files)} email(s) in '{OUTPUT_DIR}'.")
    if files:
        with open(os.path.join(OUTPUT_DIR, files[0]), encoding="utf-8") as f:
            print(f.read(400))
```