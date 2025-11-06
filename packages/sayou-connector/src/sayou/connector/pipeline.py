from typing import List, Deque, Set
from collections import deque
from sayou.core.base_component import BaseComponent
from sayou.connector.interfaces.base_seeder import BaseSeeder
from sayou.connector.interfaces.base_fetcher import BaseFetcher
from sayou.connector.interfaces.base_generator import BaseGenerator

class Pipeline(BaseComponent):
    """
    (Orchestrator) Seeder, Fetcher, Generator를
    '조립'하여 Nutch와 유사한 크롤링 파이프라인을 실행합니다.
    """
    component_name = "ConnectorPipeline"

    def __init__(self, 
        seeder: BaseSeeder,
        fetcher: BaseFetcher,
        generator: BaseGenerator = None
    ): # Generator는 선택적
        
        self.seeder = seeder
        self.fetcher = fetcher
        self.generator = generator
        self._log("Pipeline initialized with components.")

    def initialize(self, **kwargs):
        self.seeder.initialize(**kwargs)
        self.fetcher.initialize(**kwargs)
        if self.generator:
            self.generator.initialize(**kwargs) # 👈 (HtmlLinkGenerator가 base_url을 받음)

    def run(self, max_items: int = 100):
        """
        Seed -> Fetch -> (Optional) Generate 루프를 실행하고
        Fetch된 Raw Data를 반환(yield)합니다.
        
        :param max_items: 최대 수집할 아이템 수
        :return: (resource_id, raw_data) 튜플을 yield하는 제너레이터
        """
        queue: Deque[str] = deque()
        seen: Set[str] = set()
        count = 0

        # 1. Seeder가 Seed 주입
        initial_seeds = self.seeder.seed()
        for seed in initial_seeds:
            if seed not in seen:
                queue.append(seed)
                seen.add(seed)
        
        self._log(f"Seeding complete. {len(queue)} items in queue.")

        # 2. Fetch/Generate 루프
        while queue and count < max_items:
            resource_id = queue.popleft()
            
            # 3. Fetcher가 데이터 수집
            raw_data = self.fetcher.fetch(resource_id)
            
            if raw_data is None:
                continue # Fetch 실패
            
            count += 1
            yield (resource_id, raw_data) # 👈 수집된 데이터 반환
            
            # 4. Generator가 다음 URL 생성
            if self.generator:
                new_seeds = self.generator.generate(raw_data)
                for seed in new_seeds:
                    if seed not in seen:
                        queue.append(seed)
                        seen.add(seed)

        self._log(f"Run complete. Fetched {count} items.")