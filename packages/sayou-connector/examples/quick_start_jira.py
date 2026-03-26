# ── Setup
"""
Collect Jira issues and archive them as Markdown files using
`TransferPipeline`.

`JiraGenerator` queries issues using JQL (Jira Query Language).
`JiraFetcher` retrieves full issue details — summary, description, status,
priority, assignee, and all comments — and formats them as Markdown.

Install the dependency before running with a real project:

```bash
pip install atlassian-python-api
python quick_start_jira.py
```

The example below mocks all API calls so it runs without any credentials.
Remove `setup_mock()`, set the environment variables below, and point
`source` at your project key to go live.

**Create an Atlassian API token:**
https://id.atlassian.com/manage-profile/security/api-tokens
"""
import json
import os
import sys
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline

OUTPUT_DIR = "./sayou_archive/jira"


# ── Mock Setup
"""
`JiraGenerator` calls `Jira.jql()` to list issues.
`JiraFetcher` calls `Jira.issue()` to fetch each issue's full detail
including comments.

The mock simulates a project with two issues, one with a comment thread.

To switch to live mode: delete this function and its call below.
"""


def setup_mock():
    mock_jira = MagicMock()

    mock_jira.jql.return_value = {
        "issues": [
            {
                "key": "ENG-101",
                "fields": {
                    "summary": "Improve chunking throughput by 30%",
                    "priority": {"name": "High"},
                },
            },
            {
                "key": "ENG-102",
                "fields": {
                    "summary": "Add TypeScript language splitter",
                    "priority": {"name": "Medium"},
                },
            },
        ]
    }

    mock_jira.issue.return_value = {
        "fields": {
            "summary": "Improve chunking throughput by 30%",
            "description": "Profile and optimise the recursive splitter hot path.",
            "status": {"name": "In Progress"},
            "priority": {"name": "High"},
            "assignee": {"displayName": "Alice"},
            "reporter": {"displayName": "Bob"},
            "created": "2024-01-10T09:00:00.000+0000",
            "comment": {
                "comments": [
                    {
                        "author": {"displayName": "Carol"},
                        "body": "Bottleneck confirmed in TextSegmenter.recursive_split.",
                    },
                    {
                        "author": {"displayName": "Alice"},
                        "body": "Working on a fix — ETA end of sprint.",
                    },
                ]
            },
        }
    }

    mock_atlassian = MagicMock()
    mock_atlassian.Jira.return_value = mock_jira
    sys.modules["atlassian"] = mock_atlassian


# ── Collect Project Issues
"""
`source` format: `jira://{PROJECT_KEY}`

Leave the key empty (`jira://`) to collect issues assigned to the current
user across all projects.

Each issue is written as one Markdown file that includes the full
description and comment thread.
"""
setup_mock()

stats = TransferPipeline.process(
    source="jira://ENG",
    destination=OUTPUT_DIR,
    strategies={"connector": "jira"},
    url=os.environ.get("JIRA_URL", "https://mock.atlassian.net"),
    username=os.environ.get("JIRA_USERNAME", "user@example.com"),
    token=os.environ.get("JIRA_TOKEN", "mock-token"),
    limit=20,
)

print("=== Collect Project Issues ===")
print(json.dumps(stats, indent=2))


# ── Collect with Custom JQL
"""
Override the default JQL by passing a `jql` keyword argument.  Any valid
Jira Query Language expression is accepted.
"""
setup_mock()

stats_custom = TransferPipeline.process(
    source="jira://ENG",
    destination=f"{OUTPUT_DIR}/high_priority",
    strategies={"connector": "jira"},
    url=os.environ.get("JIRA_URL", "https://mock.atlassian.net"),
    username=os.environ.get("JIRA_USERNAME", "user@example.com"),
    token=os.environ.get("JIRA_TOKEN", "mock-token"),
    jql='project = "ENG" AND priority = High AND status != Done ORDER BY updated DESC',
    limit=10,
)

print("=== Custom JQL ===")
print(json.dumps(stats_custom, indent=2))


# ── Validate Output
"""
Each issue produces one Markdown file.  Open one to verify that the
summary, description, and comments were captured.
"""
if os.path.isdir(OUTPUT_DIR):
    files = [
        n for n in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, n))
    ]
    print(f"\nArchived {len(files)} issue(s) in '{OUTPUT_DIR}'.")
    if files:
        sample_path = os.path.join(OUTPUT_DIR, files[0])
        with open(sample_path, encoding="utf-8") as f:
            print(f.read(400))  # ── Setup
"""
Collect Jira issues and archive them as Markdown files using
`TransferPipeline`.

`JiraGenerator` queries issues using JQL (Jira Query Language).
`JiraFetcher` retrieves full issue details — summary, description, status,
priority, assignee, and all comments — and formats them as Markdown.

Install the dependency before running with a real project:

```bash
pip install atlassian-python-api
python quick_start_jira.py
```

The example below mocks all API calls so it runs without any credentials.
Remove `setup_mock()`, set the environment variables below, and point
`source` at your project key to go live.

**Create an Atlassian API token:**
https://id.atlassian.com/manage-profile/security/api-tokens
"""
import json
import os
import sys
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline

OUTPUT_DIR = "./sayou_archive/jira"


# ── Mock Setup
"""
`JiraGenerator` calls `Jira.jql()` to list issues.
`JiraFetcher` calls `Jira.issue()` to fetch each issue's full detail
including comments.

The mock simulates a project with two issues, one with a comment thread.

To switch to live mode: delete this function and its call below.
"""


def setup_mock():
    mock_jira = MagicMock()

    mock_jira.jql.return_value = {
        "issues": [
            {
                "key": "ENG-101",
                "fields": {
                    "summary": "Improve chunking throughput by 30%",
                    "priority": {"name": "High"},
                },
            },
            {
                "key": "ENG-102",
                "fields": {
                    "summary": "Add TypeScript language splitter",
                    "priority": {"name": "Medium"},
                },
            },
        ]
    }

    mock_jira.issue.return_value = {
        "fields": {
            "summary": "Improve chunking throughput by 30%",
            "description": "Profile and optimise the recursive splitter hot path.",
            "status": {"name": "In Progress"},
            "priority": {"name": "High"},
            "assignee": {"displayName": "Alice"},
            "reporter": {"displayName": "Bob"},
            "created": "2024-01-10T09:00:00.000+0000",
            "comment": {
                "comments": [
                    {
                        "author": {"displayName": "Carol"},
                        "body": "Bottleneck confirmed in TextSegmenter.recursive_split.",
                    },
                    {
                        "author": {"displayName": "Alice"},
                        "body": "Working on a fix — ETA end of sprint.",
                    },
                ]
            },
        }
    }

    mock_atlassian = MagicMock()
    mock_atlassian.Jira.return_value = mock_jira
    sys.modules["atlassian"] = mock_atlassian


# ── Collect Project Issues
"""
`source` format: `jira://{PROJECT_KEY}`

Leave the key empty (`jira://`) to collect issues assigned to the current
user across all projects.

Each issue is written as one Markdown file that includes the full
description and comment thread.
"""
setup_mock()

stats = TransferPipeline.process(
    source="jira://ENG",
    destination=OUTPUT_DIR,
    strategies={"connector": "jira"},
    url=os.environ.get("JIRA_URL", "https://mock.atlassian.net"),
    username=os.environ.get("JIRA_USERNAME", "user@example.com"),
    token=os.environ.get("JIRA_TOKEN", "mock-token"),
    limit=20,
)

print("=== Collect Project Issues ===")
print(json.dumps(stats, indent=2))


# ── Collect with Custom JQL
"""
Override the default JQL by passing a `jql` keyword argument.  Any valid
Jira Query Language expression is accepted.
"""
setup_mock()

stats_custom = TransferPipeline.process(
    source="jira://ENG",
    destination=f"{OUTPUT_DIR}/high_priority",
    strategies={"connector": "jira"},
    url=os.environ.get("JIRA_URL", "https://mock.atlassian.net"),
    username=os.environ.get("JIRA_USERNAME", "user@example.com"),
    token=os.environ.get("JIRA_TOKEN", "mock-token"),
    jql='project = "ENG" AND priority = High AND status != Done ORDER BY updated DESC',
    limit=10,
)

print("=== Custom JQL ===")
print(json.dumps(stats_custom, indent=2))


# ── Validate Output
"""
Each issue produces one Markdown file.  Open one to verify that the
summary, description, and comments were captured.
"""
if os.path.isdir(OUTPUT_DIR):
    files = [
        n for n in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, n))
    ]
    print(f"\nArchived {len(files)} issue(s) in '{OUTPUT_DIR}'.")
    if files:
        sample_path = os.path.join(OUTPUT_DIR, files[0])
        with open(sample_path, encoding="utf-8") as f:
            print(f.read(400))
