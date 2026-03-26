!!! abstract "Source"
    Synced from [`packages/sayou-connector/examples/quick_start_youtube_google.py`](https://github.com/sayouzone/sayou-fabric/blob/main/packages/sayou-connector/examples/quick_start_youtube_google.py).

## Setup

Collect metadata from your YouTube liked videos or channel uploads using
`TransferPipeline` with OAuth authentication.

`GoogleYoutubeGenerator` scans your YouTube library (`target="liked"` or
`target="uploads"`) and yields one task per video.
`GoogleYoutubeFetcher` calls the YouTube Data API v3 to retrieve the full
snippet, statistics, and tags for each video, returning a structured dict.

Install the dependencies before running with a real account:

```bash
pip install google-api-python-client google-auth
python quick_start_youtube_google.py
```

The example below mocks all Google API calls so it runs without any OAuth
token.  Remove `setup_mock()`, generate a `token.json` with the
`youtube.readonly` scope, and set `GOOGLE_TOKEN_PATH` to go live.

```python
import json
import os
import sys
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline

OUTPUT_DIR = "./sayou_archive/youtube_google"
```

## Mock Setup

`GoogleYoutubeGenerator` (target="liked") calls:
  - `service.videos().list(myRating="like", maxResults=…).execute()`

`GoogleYoutubeGenerator` (target="uploads") calls:
  - `service.channels().list(mine=True, …).execute()`
  - `service.playlistItems().list(playlistId=uploads_playlist_id, …).execute()`

`GoogleYoutubeFetcher` calls:
  - `service.videos().list(part="snippet,statistics", id=video_id).execute()`

To switch to live mode: delete this function and its call below.

```python
def setup_mock():
    mock_service = MagicMock()

    # Liked videos list
    mock_service.videos.return_value.list.return_value.execute.return_value = {
        "items": [
            {"id": "dQw4w9WgXcQ", "snippet": {"title": "Never Gonna Give You Up"}},
            {"id": "9bZkp7q19f0", "snippet": {"title": "Gangnam Style"}},
        ]
    }

    # Video detail fetch
    mock_service.videos.return_value.list.return_value.execute.side_effect = [
        # First call: liked list (generator)
        {
            "items": [
                {"id": "dQw4w9WgXcQ", "snippet": {"title": "Never Gonna Give You Up"}},
                {"id": "9bZkp7q19f0", "snippet": {"title": "Gangnam Style"}},
            ]
        },
        # Subsequent calls: detail fetch (fetcher, one per video)
        {
            "items": [
                {
                    "snippet": {
                        "title": "Never Gonna Give You Up",
                        "channelTitle": "Rick Astley",
                        "description": "Official music video.",
                        "tags": ["rick", "roll"],
                    },
                    "statistics": {
                        "viewCount": "1400000000",
                        "likeCount": "15000000",
                    },
                }
            ]
        },
        {
            "items": [
                {
                    "snippet": {
                        "title": "Gangnam Style",
                        "channelTitle": "PSY",
                        "description": "Official MV.",
                        "tags": ["psy", "kpop"],
                    },
                    "statistics": {
                        "viewCount": "4700000000",
                        "likeCount": "24000000",
                    },
                }
            ]
        },
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

## Collect Liked Videos

`source` format: `youtube://liked` (or any `youtube://…` URI).
`target="liked"` collects videos you have liked.
`target="uploads"` collects videos from your own channel.

`packet.data["content"]` is the raw API response dict including snippet
and statistics.  `packet.data["meta"]` contains title, channel, tags,
view count, and a description snippet.

```python
setup_mock()

stats = TransferPipeline.process(
    source="youtube://liked",
    destination=OUTPUT_DIR,
    strategies={"connector": "youtube"},
    google_token_path=os.environ.get("GOOGLE_TOKEN_PATH", "./token.json"),
    target="liked",
    limit=20,
)

print("=== Collect Liked Videos ===")
print(json.dumps(stats, indent=2))
```

## Collect Channel Uploads

Switch to `target="uploads"` to collect your own channel's upload history.

```python
setup_mock()

stats_uploads = TransferPipeline.process(
    source="youtube://uploads",
    destination=f"{OUTPUT_DIR}/uploads",
    strategies={"connector": "youtube"},
    google_token_path=os.environ.get("GOOGLE_TOKEN_PATH", "./token.json"),
    target="uploads",
    limit=50,
)

print("=== Collect Channel Uploads ===")
print(json.dumps(stats_uploads, indent=2))
```

## Validate Output

Each video produces one JSON file containing the full API response and
extracted metadata (title, channel, tags, view count).

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