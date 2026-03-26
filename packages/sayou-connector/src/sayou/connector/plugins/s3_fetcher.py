from typing import Any, Dict

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher

try:
    import boto3
except ImportError:
    boto3 = None


@register_component("fetcher")
class S3Fetcher(BaseFetcher):
    """
    Downloads an object from S3.
    """

    component_name = "S3Fetcher"
    SUPPORTED_TYPES = ["s3"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if uri.startswith("s3-object://") else 0.0

    def _do_fetch(self, task: SayouTask) -> Dict[str, Any]:
        bucket = task.params["bucket"]
        key = task.params["key"]
        aws_config = task.params.get("aws_config", {})

        s3 = boto3.client("s3", **aws_config)
        response = s3.get_object(Bucket=bucket, Key=key)
        raw_body = response["Body"].read()
        content_type = response.get("ContentType", "")

        try:
            content = raw_body.decode("utf-8")
        except UnicodeDecodeError:
            content = raw_body

        filename = key.split("/")[-1]

        return {
            "content": content,
            "meta": {
                "source": "s3",
                "file_id": key,
                "title": filename,
                "bucket": bucket,
                "mime_type": content_type,
                "size": task.params.get("size"),
                "extension": "",
            },
        }
