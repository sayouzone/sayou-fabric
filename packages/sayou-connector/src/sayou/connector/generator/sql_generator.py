from typing import Iterator

from ..core.models import FetchTask, FetchResult
from ..interfaces.base_generator import BaseGenerator

class SqlGenerator(BaseGenerator):
    """
    (Tier 2) SQL 쿼리를 생성하여 DB 수집을 지시하는 생성기.
    Pagination(Batch Fetch)을 지원합니다.
    """
    component_name = "SqlGenerator"
    SUPPORTED_TYPES = ["sql_scan"]

    def initialize(
        self,
        source: str,
        query: str,
        batch_size: int = 1000,
        **kwargs
    ):
        self.conn_str = source
        self.base_query = query.strip().rstrip(";")
        self.batch_size = batch_size
        self.current_offset = 0
        self.stop_flag = False

    def generate(self) -> Iterator[FetchTask]:
        while not self.stop_flag:
            # 간단한 Pagination 쿼리 생성 (Dialect에 따라 다를 수 있음, 여기선 SQLite/Standard 기준)
            paginated_query = f"{self.base_query} LIMIT {self.batch_size} OFFSET {self.current_offset}"
            
            task = FetchTask(
                source_type="sqlite", # Fetcher 라우팅 키
                uri=self.conn_str,
                params={"query": paginated_query}
            )
            
            yield task
            
            # 다음 루프 준비 (feedback에서 멈춤 신호를 받기 전까지 일단 yield 후 대기)
            # 실제 파이프라인 구현에 따라 여기서 yield가 멈추면 다음 feedback이 올 때까지 대기됨.
            self.current_offset += self.batch_size

    def feedback(self, result: FetchResult):
        """결과가 없으면(0건) 종료 플래그 설정"""
        if not result.success or not result.data:
            self.stop_flag = True
            return
            
        # 가져온 데이터가 배치 사이즈보다 작으면 마지막 페이지임
        rows = result.data
        if len(rows) < self.batch_size:
            self.stop_flag = True