!!! abstract "Source"
    Synced from [`packages/sayou-connector/examples/quick_start_github.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-connector/examples/quick_start_github.py).

## Setup

Collect files or issues from a GitHub repository and archive them using
`TransferPipeline`.

`GithubGenerator` traverses the repository file tree (`target="code"`) or
lists issue threads (`target="issues"`).  `GithubFetcher` downloads the
raw content of each file (decoded as UTF-8 where possible) or formats each
issue as a Markdown document with title, body, labels, and comments.

Install the dependency before running with a real repository:

```bash
pip install PyGithub
python quick_start_github.py
```

The example below mocks all GitHub API calls so it runs without a token.
Remove `setup_mock()`, set `GITHUB_TOKEN`, and update `source` to go live.

**Personal Access Token (PAT):**
Required for private repositories.  For public repositories it avoids
rate-limiting.  Create one at https://github.com/settings/tokens.

```python
import json
import os
import sys
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline

OUTPUT_DIR = "./sayou_archive/github"
```

## Mock Setup

`GithubGenerator` calls `Github(auth=…).get_repo(…).get_contents(path)`.

The mock returns two Python files at the root and raises a different
response when a specific sub-path is requested (simulating a directory
entry with nested files).

`GithubFetcher` calls `repo.get_contents(file_path)` and reads
`.decoded_content`.

The same mock is reused for both `target="code"` and `target="issues"`.

To switch to live mode: delete this function and its call below.

```python
def setup_mock():
    mock_file_1 = MagicMock()
    mock_file_1.type = "file"
    mock_file_1.path = "src/pipeline.py"
    mock_file_1.name = "pipeline.py"
    mock_file_1.size = 8192
    mock_file_1.decoded_content = (
        b"# ChunkingPipeline\nclass ChunkingPipeline:\n    pass\n"
    )

    mock_file_2 = MagicMock()
    mock_file_2.type = "file"
    mock_file_2.path = "src/splitter.py"
    mock_file_2.name = "splitter.py"
    mock_file_2.size = 4096
    mock_file_2.decoded_content = (
        b"# RecursiveSplitter\nclass RecursiveSplitter:\n    pass\n"
    )

    mock_repo = MagicMock()
    mock_repo.get_contents.side_effect = lambda path: (
        [mock_file_1, mock_file_2] if path == "" else mock_file_1
    )

    # Issue mock (used when target="issues")
    mock_issue = MagicMock()
    mock_issue.number = 42
    mock_issue.title = "Improve chunking throughput by 30%"
    mock_issue.body = "Profile the recursive splitter hot path."
    mock_issue.state = "open"
    mock_issue.html_url = "https://github.com/sayouzone/sayou-fabric/issues/42"
    mock_issue.user.login = "alice"
    mock_issue.labels = []
    mock_issue.get_comments.return_value = []
    mock_repo.get_issues.return_value = [mock_issue]

    mock_g = MagicMock()
    mock_g.get_repo.return_value = mock_repo

    mock_auth = MagicMock()
    mock_github = MagicMock()
    mock_github.Github.return_value = mock_g
    mock_github.Auth = mock_auth

    sys.modules["github"] = mock_github
```

## Collect Repository Code

`source` format: `github://{owner}/{repo}`

Use `path` to restrict traversal to a sub-directory within the repository.
Use `extensions` to collect only specific file types.
`limit=0` means no cap on file count.

```python
setup_mock()

stats_code = TransferPipeline.process(
    source="github://sayouzone/sayou-fabric",
    destination=f"{OUTPUT_DIR}/code",
    strategies={"connector": "github"},
    token=os.environ.get("GITHUB_TOKEN", "ghp-mock-token"),
    target="code",
    path="src",
    extensions=[".py"],
    limit=50,
)

print("=== Collect Repository Code ===")
print(json.dumps(stats_code, indent=2))
```

## Collect Issues

Switch to `target="issues"` to collect issue threads instead of source
files.  Each issue is archived as a self-contained Markdown document.

```python
setup_mock()

stats_issues = TransferPipeline.process(
    source="github://sayouzone/sayou-fabric",
    destination=f"{OUTPUT_DIR}/issues",
    strategies={"connector": "github"},
    token=os.environ.get("GITHUB_TOKEN", "ghp-mock-token"),
    target="issues",
    limit=20,
)

print("=== Collect Issues ===")
print(json.dumps(stats_issues, indent=2))
```

## Validate Output

Code files are archived with their original extension.  Issue files are
Markdown documents.  Inspect a sample to confirm the content is correct.

```python
for label, subdir in [("code", "code"), ("issues", "issues")]:
    path = os.path.join(OUTPUT_DIR, subdir)
    if os.path.isdir(path):
        files = [n for n in os.listdir(path) if os.path.isfile(os.path.join(path, n))]
        print(f"\n[{label}] Archived {len(files)} file(s) in '{path}'.")
        if files:
            sample = os.path.join(path, files[0])
            with open(sample, encoding="utf-8") as f:
                print(f.read(300))
```