# ── Setup
"""
Collect Slack channel history and archive each message as a Markdown file
using `TransferPipeline`.

`SlackGenerator` fetches recent messages from a channel (including thread
replies).  `SlackFetcher` formats each message with sender, timestamp,
permalink, and thread replies as a structured Markdown document.

Install the dependency before running with a real workspace:

```bash
pip install slack-sdk
python quick_start_slack.py
```

The example below mocks all Slack API calls so it runs without any token.
Remove `setup_mock()`, set `SLACK_BOT_TOKEN`, and update `source` to go live.

**Required Bot Token Scopes:**
`channels:history`, `channels:read`, `conversations.replies`
"""
import json
import os
import sys
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline

OUTPUT_DIR = "./sayou_archive/slack"


# ── Mock Setup
"""
`SlackGenerator` calls:
  - `WebClient.conversations_list()` — resolve channel name → ID
  - `WebClient.conversations_history()` — fetch messages

`SlackFetcher` calls:
  - `WebClient.conversations_replies()` — fetch thread replies (when reply_count > 0)

The mock simulates a `#general` channel with two messages, one of which has
a thread reply.

To switch to live mode: delete this function and its call below.
"""


def setup_mock():
    mock_client = MagicMock()

    mock_client.conversations_list.return_value = {
        "channels": [{"id": "C001", "name": "general"}]
    }

    mock_client.conversations_history.return_value = {
        "messages": [
            {
                "ts": "1704067200.000001",
                "user": "U001",
                "text": "Has anyone reviewed the latest chunking PR?",
                "reply_count": 1,
            },
            {
                "ts": "1704067300.000002",
                "user": "U002",
                "text": "Deployment to staging is scheduled for Friday.",
                "reply_count": 0,
            },
        ]
    }

    mock_client.conversations_replies.return_value = {
        "messages": [
            {
                "ts": "1704067200.000001",
                "user": "U001",
                "text": "Original message.",
            },
            {
                "ts": "1704067250.000010",
                "user": "U003",
                "text": "Yes, LGTM! Merging now.",
            },
        ]
    }

    mock_sdk = MagicMock()
    mock_sdk.WebClient.return_value = mock_client

    mock_errors = MagicMock()
    mock_errors.SlackApiError = Exception

    sys.modules["slack_sdk"] = mock_sdk
    sys.modules["slack_sdk.errors"] = mock_errors


# ── Collect Channel History
"""
`source` format: `slack://{channel_name}` (without the `#` prefix).
`limit` controls the number of messages fetched (default: 20).

Each message is archived as a Markdown file containing the sender, time,
link, message body, and any thread replies.
"""
setup_mock()

stats = TransferPipeline.process(
    source="slack://general",
    destination=OUTPUT_DIR,
    strategies={"connector": "slack"},
    token=os.environ.get("SLACK_BOT_TOKEN", "xoxb-mock-token"),
    limit=10,
)

print("=== Collect Channel History ===")
print(json.dumps(stats, indent=2))


# ── Collect Multiple Channels
"""
Run the pipeline once per channel.  Point each run at a sub-directory to
keep the archives separated by channel.
"""
channels = ["slack://general", "slack://engineering", "slack://random"]

total = {"read": 0, "written": 0, "failed": 0}
for channel in channels:
    setup_mock()
    name = channel.replace("slack://", "")
    s = TransferPipeline.process(
        source=channel,
        destination=f"{OUTPUT_DIR}/{name}",
        strategies={"connector": "slack"},
        token=os.environ.get("SLACK_BOT_TOKEN", "xoxb-mock-token"),
        limit=5,
    )
    for k in total:
        total[k] += s.get(k, 0)

print("=== Collect Multiple Channels ===")
print(json.dumps(total, indent=2))


# ── Validate Output
"""
Each message produces one Markdown file.  Open one to confirm the full
thread context was captured.
"""
if os.path.isdir(OUTPUT_DIR):
    files = [
        n for n in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, n))
    ]
    print(f"\nArchived {len(files)} message(s) in '{OUTPUT_DIR}'.")
    if files:
        sample_path = os.path.join(OUTPUT_DIR, files[0])
        with open(sample_path, encoding="utf-8") as f:
            print(f.read(400))
