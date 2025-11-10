from typing import Any, List, Deque, Set, Optional, Dict
from collections import deque
from sayou.core.base_component import BaseComponent
from .interfaces.base_seeder import BaseSeeder
from .interfaces.base_fetcher import BaseFetcher
from .interfaces.base_generator import BaseGenerator

class ConnectorPipeline(BaseComponent):
    """
    (Orchestrator) Seeder, Fetcher, Generator를 조립합니다.
    'run' 메서드는 RAG 모드(단일 실행)와 크롤링 모드(배치 실행)를 모두 지원합니다.
    """
    component_name = "ConnectorPipeline"

    def __init__(self, 
        fetcher: BaseFetcher,
        seeder: Optional[BaseSeeder] = None,
        generator: Optional[BaseGenerator] = None
    ):
        self.seeder = seeder
        self.fetcher = fetcher
        self.generator = generator
        self._log("Pipeline initialized with components.")

    def initialize(self, **kwargs):
        """[정상] 컴포넌트들을 None-safe하게 초기화합니다."""
        if self.seeder:
            self.seeder.initialize(**kwargs)
        
        self.fetcher.initialize(**kwargs) # 👈 RAG에 필수
        
        if self.generator:
            self.generator.initialize(**kwargs)

    def run(self, **kwargs) -> Dict[str, Any]:
        """
        [수정] 파이프라인의 단일 진입점(Router)입니다.
        kwargs에 'data_source'가 있으면 RAG 모드로,
        없으면 크롤링 모드로 실행됩니다.
        """
        data_source = kwargs.get("data_source")
        
        if data_source is not None:
            # 1. RAG 모드 (단일 실행)
            return self._run_single_fetch(data_source)
        else:
            # 2. 크롤링 모드 (배치 실행)
            max_items = kwargs.get("max_items", 100)
            return self._run_crawl(max_items)

    def _run_single_fetch(self, data_source: Any) -> Dict[str, Any]:
        """
        [신규] RAG 예제를 위한 단일 페치 로직입니다.
        """
        self._log(f"Running in single-fetch mode for {data_source}")
        
        raw_data = None
        # BasicRAG가 (target, query) 튜플을 전달하는 경우
        if isinstance(data_source, tuple) and len(data_source) == 2:
            # BaseFetcher.fetch() (뼈대)를 호출합니다.
            raw_data = self.fetcher.fetch(target=data_source[0], query=data_source[1])
        else:
            raw_data = self.fetcher.fetch(data_source) # query 없이 호출

        if raw_data is None:
            raise RuntimeError("Connector failed: empty response")

        # ApiFetcher가 반환한 'raw_data'의 원본을 확인합니다.
        # print("\n" + "="*20 + " [DEBUG] RAW_DATA FROM CONNECTOR " + "="*20)
        # print(f"Data Type: {type(raw_data)}")
        # print(f"Data Length: {len(raw_data)}")
        # print("\n--- RAW_DATA (START) ---\n")
        # print(raw_data[:500]) # 👈 앞 500자 출력
        # print("\n--- RAW_DATA (END) ---\n")
        # print(raw_data[-500:]) # 👈 뒤 500자 출력
        # print("="*66 + "\n")

        return {"raw_data": raw_data}

    def _run_crawl(self, max_items: int) -> Dict[str, Any]:
        """
        [수정] 기존의 크롤링(yield) 로직입니다.
        """
        if not self.seeder:
            raise ValueError("Seeder must be provided for crawl mode.")
            
        self._log(f"Running in crawl mode (max: {max_items} items)...")
        
        crawled_results: List[tuple] = []
        queue: Deque[str] = deque()
        seen: Set[str] = set()
        count = 0

        # ( ... 기존 크롤링 로직 ... )
        initial_seeds = self.seeder.seed()
        for seed in initial_seeds:
            if seed not in seen:
                queue.append(seed)
                seen.add(seed)
        
        while queue and count < max_items:
            resource_id = queue.popleft()
            
            # BaseFetcher.fetch() (뼈대)를 호출합니다.
            raw_data = self.fetcher.fetch(resource_id) # query 없이 호출
            
            if raw_data is None:
                continue 
            
            count += 1
            crawled_results.append((resource_id, raw_data))
            
            if self.generator:
                new_seeds = self.generator.generate(raw_data)
                # ( ... new_seeds 로직 ... )

        return {"crawled_data": crawled_results}