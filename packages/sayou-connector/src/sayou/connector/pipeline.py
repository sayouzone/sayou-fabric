from typing import List, Dict, Optional, Iterator, Type

from sayou.core.base_component import BaseComponent

from .core.models import FetchResult
from .interfaces.base_generator import BaseGenerator
from .interfaces.base_fetcher import BaseFetcher
from .generator.file_generator import FileGenerator
from .generator.sql_generator import SqlGenerator
from .generator.web_generator import WebCrawlGenerator
from .fetcher.file_fetcher import FileFetcher
from .fetcher.sql_fetcher import SqliteFetcher
from .fetcher.web_fetcher import SimpleWebFetcher

class ConnectorPipeline(BaseComponent):
    """
    (Orchestrator) Generator와 Fetcher를 연결하여 데이터를 수집하는 파이프라인.
    """
    component_name = "ConnectorPipeline"

    def __init__(
        self, 
        extra_generators: Optional[List[BaseGenerator]] = None,
        extra_fetchers: Optional[List[BaseFetcher]] = None
    ):
        self.gen_map: Dict[str, BaseGenerator] = {}
        self.fetch_map: Dict[str, BaseFetcher] = {}

        # 1. 기본 컴포넌트 등록
        self._register(self.gen_map, [FileGenerator(), SqlGenerator(), WebCrawlGenerator()])
        self._register(self.fetch_map, [FileFetcher(), SqliteFetcher(), SimpleWebFetcher()])

        # 2. 추가 컴포넌트 등록
        if extra_generators: self._register(self.gen_map, extra_generators)
        if extra_fetchers: self._register(self.fetch_map, extra_fetchers)

    def _register(self, target_map, components):
        for c in components:
            for t in getattr(c, "SUPPORTED_TYPES", []):
                target_map[t] = c

    def initialize(self, **kwargs):
        # (필요시 전역 초기화)
        pass

    def run(self, source: str, strategy: str = "local_scan", **kwargs) -> Iterator[FetchResult]:
        """
        Args:
            source: 수집 대상 루트 (파일 경로, URL 등)
            strategy: 사용할 Generator 전략 ('local_scan' 등)
            **kwargs: Generator에 전달할 상세 설정 (extensions, name_pattern 등)
        """
        # 1. Generator 선택
        generator = self.gen_map.get(strategy)
        if not generator:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        # 2. Generator 초기화 (Config 주입)
        # 여기서 'root_path', 'extensions' 등이 주입됨
        generator.initialize(source=source, **kwargs)

        self._log(f"Connector started using strategy '{strategy}' on '{source}'")

        # 3. Loop execution
        count = 0
        for task in generator.generate():
            # 4. Fetcher 라우팅
            fetcher = self.fetch_map.get(task.source_type)
            if not fetcher:
                self._log(f"Skipping task {task.uri}: No fetcher for type '{task.source_type}'")
                continue

            # 5. Fetch 수행
            result = fetcher.fetch(task)
            
            if result.success:
                count += 1
                yield result
                
                # Generator에게 피드백 (파일 탐색엔 불필요하지만 구조상 존재)
                generator.feedback(result)
            else:
                self._log(f"Fetch failed: {result.error}")

        self._log(f"Connector finished. Total fetched: {count}")