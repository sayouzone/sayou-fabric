from typing import Iterator

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_generator import BaseGenerator

try:
    import boto3
except ImportError:
    boto3 = None


@register_component("generator")
class S3Generator(BaseGenerator):
    """
    Scans AWS S3 Bucket for objects.
    Supports recursive scanning via Prefix.
    """

    component_name = "S3Generator"
    SUPPORTED_TYPES = ["s3"]

    @classmethod
    def can_handle(cls, source: str) -> float:
        return 1.0 if source.startswith("s3://") else 0.0

    def _do_generate(self, source: str, **kwargs) -> Iterator[SayouTask]:
        if not boto3:
            raise ImportError("Please install boto3: pip install boto3")

        # 1. Parsing Address (s3://bucket/prefix)
        path_parts = source.replace("s3://", "").split("/", 1)
        bucket_name = path_parts[0]
        prefix = path_parts[1] if len(path_parts) > 1 else ""

        # 2. AWS Client
        aws_access_key = kwargs.get("aws_access_key_id")
        aws_secret_key = kwargs.get("aws_secret_access_key")
        region_name = kwargs.get("region_name", "ap-northeast-2")

        s3 = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region_name,
        )

        self._log(f"Scanning S3 bucket: {bucket_name}, Prefix: {prefix}")

        # 3. Pagination (for files over 1000)
        paginator = s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

        limit = int(kwargs.get("limit", 0))
        count = 0

        for page in pages:
            if "Contents" not in page:
                continue

            for obj in page["Contents"]:
                key = obj["Key"]

                if key.endswith("/"):
                    continue

                yield SayouTask(
                    uri=f"s3-object://{bucket_name}/{key}",
                    source_type="s3",
                    params={
                        "bucket": bucket_name,
                        "key": key,
                        "size": obj["Size"],
                        "last_modified": obj["LastModified"],
                        "aws_config": {
                            "aws_access_key_id": aws_access_key,
                            "aws_secret_access_key": aws_secret_key,
                            "region_name": region_name,
                        },
                    },
                )

                count += 1
                if limit > 0 and count >= limit:
                    return
