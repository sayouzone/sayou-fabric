# ── Setup
"""
Collect objects from an AWS S3 bucket and archive them using
`TransferPipeline`.

`S3Generator` paginates through all objects under a given prefix using the
`list_objects_v2` API.  `S3Fetcher` downloads each object as UTF-8 text
(binary files are returned as `bytes`).

Install the dependency before running with a real bucket:

```bash
pip install boto3
python quick_start_s3.py
```

The example below mocks all AWS API calls so it runs without any
credentials.  Remove `setup_mock()`, set the environment variables below,
and update `source` with your bucket name to go live.

**Credential options (in order of preference):**
1. IAM instance profile — no environment variables needed inside EC2 / ECS.
2. Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`.
3. `~/.aws/credentials` file configured with `aws configure`.
"""
import json
import os
import sys
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline

OUTPUT_DIR = "./sayou_archive/s3"


# ── Mock Setup
"""
`S3Generator` calls `boto3.client("s3").get_paginator("list_objects_v2")`
then iterates the paginator.
`S3Fetcher` calls `s3.get_object(Bucket=…, Key=…)`.

The mock simulates a bucket with three objects across two paginator pages.
Object content is a fixed UTF-8 string.

To switch to live mode: delete this function and its call below.
"""


def setup_mock():
    mock_body = MagicMock()
    mock_body.read.return_value = b"Mock S3 object content.\nLine two of the file."

    mock_client = MagicMock()

    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [
        {
            "Contents": [
                {"Key": "docs/readme.txt", "Size": 512},
                {"Key": "docs/architecture.md", "Size": 1024},
            ]
        },
        {
            "Contents": [
                {"Key": "docs/changelog.txt", "Size": 256},
            ]
        },
    ]
    mock_client.get_paginator.return_value = mock_paginator
    mock_client.get_object.return_value = {
        "Body": mock_body,
        "ContentType": "text/plain",
    }

    mock_boto3 = MagicMock()
    mock_boto3.client.return_value = mock_client
    sys.modules["boto3"] = mock_boto3


# ── Collect a Bucket Prefix
"""
`source` format: `s3://{bucket}/{prefix}`

`prefix` acts like a directory path — only keys that start with it are
collected.  Use an empty prefix (`s3://my-bucket/`) to collect the entire
bucket.

`limit=0` disables the object count cap (collect everything).
"""
setup_mock()

stats = TransferPipeline.process(
    source="s3://my-data-bucket/docs/",
    destination=OUTPUT_DIR,
    strategies={"connector": "s3"},
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    region_name=os.environ.get("AWS_DEFAULT_REGION", "ap-northeast-2"),
    limit=0,
)

print("=== Collect a Bucket Prefix ===")
print(json.dumps(stats, indent=2))


# ── Collect with Object Limit
"""
Set `limit` to a positive integer to stop after that many objects.
Useful for testing or for collecting only the most recent uploads.
"""
setup_mock()

stats_limited = TransferPipeline.process(
    source="s3://my-data-bucket/logs/",
    destination=f"{OUTPUT_DIR}/logs",
    strategies={"connector": "s3"},
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    region_name=os.environ.get("AWS_DEFAULT_REGION", "ap-northeast-2"),
    limit=50,
)

print("=== Collect with Object Limit ===")
print(json.dumps(stats_limited, indent=2))


# ── Validate Output
"""
Each S3 object produces one file in `destination`.  Inspect a sample to
confirm the content was decoded and written correctly.
"""
if os.path.isdir(OUTPUT_DIR):
    files = [
        n for n in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, n))
    ]
    print(f"\nArchived {len(files)} object(s) in '{OUTPUT_DIR}'.")
    if files:
        sample_path = os.path.join(OUTPUT_DIR, files[0])
        with open(sample_path, encoding="utf-8") as f:
            print(f.read(200))
