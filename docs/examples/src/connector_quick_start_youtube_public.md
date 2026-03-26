!!! abstract "Source"
    Synced from [`packages/sayou-connector/examples/quick_start_youtube_public.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-connector/examples/quick_start_youtube_public.py).

## Setup

Collect transcripts and metadata from public YouTube videos using
`TransferPipeline` — no OAuth required.

`YouTubeGenerator` parses video IDs from URLs or raw IDs (comma-separated).
`YouTubeFetcher` scrapes the video page for metadata (title, channel,
views, tags) and fetches the auto-generated transcript via
`youtube-transcript-api`, returning both as a structured dict.

Install the dependencies before running with real video IDs:

```bash
pip install youtube-transcript-api requests
python quick_start_youtube_public.py
```

The example below mocks both libraries so it runs without network access.
Remove `setup_mock()` and substitute real YouTube video IDs to go live.

```python
import json
import os
import sys
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline

OUTPUT_DIR = "./sayou_archive/youtube_public"
```

## Mock Setup

`YouTubeFetcher` calls:
  - `YouTubeTranscriptApi().list(video_id)` — list available transcripts
  - `transcript_list.find_transcript(["ko", "en", …])` — select language
  - `transcript.fetch()` — download cue list

  - `requests.get(youtube_url)` — scrape HTML for metadata

The mock returns a two-cue transcript and a realistic metadata dict.

To switch to live mode: delete this function and its call below.

```python
def setup_mock():
    # Transcript cues
    mock_cue_1 = MagicMock()
    mock_cue_1.text = "Hello and welcome to this tutorial."
    mock_cue_1.start = 0.0
    mock_cue_1.duration = 3.5

    mock_cue_2 = MagicMock()
    mock_cue_2.text = "Today we are covering LLM data pipelines."
    mock_cue_2.start = 3.5
    mock_cue_2.duration = 4.2

    mock_transcript = MagicMock()
    mock_transcript.fetch.return_value = [mock_cue_1, mock_cue_2]

    mock_transcript_list = MagicMock()
    mock_transcript_list.find_transcript.return_value = mock_transcript

    mock_yt_api = MagicMock()
    mock_yt_api.return_value.list.return_value = mock_transcript_list

    mock_yt_module = MagicMock()
    mock_yt_module.YouTubeTranscriptApi = mock_yt_api
    sys.modules["youtube_transcript_api"] = mock_yt_module

    # requests mock for metadata scraping
    mock_html = """
    <meta property="og:title" content="LLM Data Pipelines Explained">
    <meta property="og:description" content="A complete guide to building LLM data pipelines.">
    <link itemprop="name" content="Tech Academy">
    <meta itemprop="datePublished" content="2024-04-01">
    <meta itemprop="interactionCount" content="125000">
    <meta name="keywords" content="LLM, data pipeline, RAG, AI">
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = mock_html

    mock_requests = MagicMock()
    mock_requests.get.return_value = mock_response
    sys.modules["requests"] = mock_requests
```

## Transfer a Single Video

`source` format: `youtube://{video_id}` or any YouTube URL.

Supported input formats (comma-separated for multiple):
  - `youtube://dQw4w9WgXcQ`                    — raw video ID
  - `https://www.youtube.com/watch?v=dQw4w9WgXcQ` — full URL
  - `https://youtu.be/dQw4w9WgXcQ`             — short URL

`packet.data["content"]` is the transcript cue list (list of dicts with
`text`, `start`, `duration`).  `packet.data["meta"]` includes title,
channel, view count, publish date, keywords, and thumbnail URL.

```python
setup_mock()

stats = TransferPipeline.process(
    source="youtube://dQw4w9WgXcQ",
    destination=OUTPUT_DIR,
    strategies={"connector": "youtube"},
)

print("=== Transfer a Single Video ===")
print(json.dumps(stats, indent=2))
```

## Transfer Multiple Videos

Pass a comma-separated list of IDs or URLs after `youtube://`.
Each video produces one archive file.

```python
setup_mock()

stats_multi = TransferPipeline.process(
    source="youtube://dQw4w9WgXcQ,9bZkp7q19f0,jNQXAC9IVRw",
    destination=f"{OUTPUT_DIR}/batch",
    strategies={"connector": "youtube"},
)

print("=== Transfer Multiple Videos ===")
print(json.dumps(stats_multi, indent=2))
```

## Validate Output

Each video produces one JSON file containing the transcript cue list and
full metadata.  The transcript can be passed directly to `ChunkingPipeline`
using the `json` strategy.

```python
if os.path.isdir(OUTPUT_DIR):
    files = [
        n for n in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, n))
    ]
    print(f"\nArchived {len(files)} video(s) in '{OUTPUT_DIR}'.")
    if files:
        with open(os.path.join(OUTPUT_DIR, files[0]), encoding="utf-8") as f:
            print(f.read(400))
```