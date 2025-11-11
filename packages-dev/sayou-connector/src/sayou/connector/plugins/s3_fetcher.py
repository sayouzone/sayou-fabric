from typing import Any
from ..interfaces.base_fetcher import BaseFetcher
from ..core.exceptions import ConnectorError

try:
    import boto3
except ImportError:
    raise ImportError("S3Fetcher requires 'boto3'. Install with 'pip install sayou-connector[aws]'")

class S3Fetcher(BaseFetcher):
    """(Tier 3) 'AWS S3'에서 객체를 가져오는 특화 어댑터."""
    component_name = "S3Fetcher"

    def initialize(self, **kwargs):
        self.s3_client = boto3.client('s3')
        self.encoding = kwargs.get("encoding", "utf-8")

    def _do_fetch(self, resource_id: str) -> Any:
        # resource_id가 "s3://bucket/key" 형태라고 가정
        if not resource_id.startswith("s3://"):
            raise ConnectorError("S3Fetcher resource_id must start with 's3://'")
        
        bucket, key = resource_id[5:].split('/', 1)
        obj = self.s3_client.get_object(Bucket=bucket, Key=key)
        
        # (간단한 예시: 텍스트 파일이라고 가정)
        return obj['Body'].read().decode(self.encoding)