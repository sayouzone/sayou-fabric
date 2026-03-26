!!! abstract "Source"
    Synced from [`packages/sayou-connector/examples/quick_start_rss.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-connector/examples/quick_start_rss.py).

## Setup

Collect articles from an RSS or Atom feed and archive them as Markdown
files using `TransferPipeline`.

`RssGenerator` parses the feed and yields one task per entry (up to
`limit`).  `RssFetcher` visits each entry's link with `trafilatura` for
full-text extraction, falling back to the feed summary if crawling fails.

Install the dependencies before running with a real feed:

```bash
pip install feedparser trafilatura
python quick_start_rss.py
```

The example below mocks both libraries for offline testing.
Remove `setup_mock()` and substitute a real `rss://` URL to go live.

```python
import json
import os
import sys
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline

OUTPUT_DIR = "./sayou_archive/rss"
```

## Mock Setup

`RssGenerator` calls `feedparser.parse()`.
`RssFetcher` calls `trafilatura.fetch_url()` and `trafilatura.extract()`.

`_MockEntry` mimics a real feedparser entry: it supports attribute access,
`.get()`, and the `in` operator so `RssFetcher` can extract all fields.

To switch to live mode: delete this function and its call below.

```python
class _MockEntry:
    def __init__(self, n: int):
        self.link = f"https://example.com/post-{n}"
        self.title = f"Article {n}: Latest Developments in AI"
        self.author = "Jane Doe"
        self.published = "Mon, 01 Jan 2024 12:00:00 +0000"
        self.summary = f"Summary of article {n}. Key findings this week."

    def get(self, key, default=""):
        return getattr(self, key, default)

    def __contains__(self, key):
        return hasattr(self, key)


def setup_mock():
    # feedparser mock
    mock_feed = MagicMock()
    mock_feed.bozo = False
    mock_feed.entries = [_MockEntry(i) for i in range(1, 4)]
    mock_feed.feed.get.return_value = "Example Tech Blog"

    mock_fp = MagicMock()
    mock_fp.parse.return_value = mock_feed
    sys.modules["feedparser"] = mock_fp

    # trafilatura mock (used by RssFetcher for full-text extraction)
    mock_tf = MagicMock()
    mock_tf.fetch_url.return_value = (
        "<html><body><p>Full article text.</p></body></html>"
    )
    mock_tf.extract.return_value = "Full article text extracted by trafilatura."
    sys.modules["trafilatura"] = mock_tf
```

## Collect a Feed

Use the `rss://` prefix with the feed URL (the protocol portion is replaced
automatically — `rss://feeds.example.com/tech` becomes
`https://feeds.example.com/tech`).

Each article is written as a separate Markdown file in `destination`.

```python
setup_mock()

stats = TransferPipeline.process(
    source="rss://feeds.example.com/tech",
    destination=OUTPUT_DIR,
    strategies={"connector": "rss"},
    limit=3,
)

print("=== Collect a Feed ===")
print(json.dumps(stats, indent=2))
```

## Collect Multiple Feeds

Run the pipeline once per feed.  Results accumulate in the same destination
directory, distinguished by the filename derived from each entry's title.

```python
feeds = [
    "rss://feeds.example.com/ai",
    "rss://feeds.example.com/devops",
]

total = {"read": 0, "written": 0, "failed": 0}
for feed in feeds:
    s = TransferPipeline.process(
        source=feed,
        destination=f"{OUTPUT_DIR}/multi",
        strategies={"connector": "rss"},
        limit=2,
    )
    for k in total:
        total[k] += s.get(k, 0)

print("=== Collect Multiple Feeds ===")
print(json.dumps(total, indent=2))
```

## Validate Output

Each feed entry produces one Markdown file.  The file includes the article
title, author, date, source link, and extracted body.

```python
if os.path.isdir(OUTPUT_DIR):
    files = [
        n for n in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, n))
    ]
    print(f"\nArchived {len(files)} article(s) in '{OUTPUT_DIR}'.")
    if files:
        sample_path = os.path.join(OUTPUT_DIR, files[0])
        with open(sample_path, encoding="utf-8") as f:
            print(f.read(300))
```