import re
from collections import deque
from typing import Iterator, Optional, Dict

from ..core.models import FetchTask, FetchResult
from ..interfaces.base_generator import BaseGenerator

class WebCrawlGenerator(BaseGenerator):
    """
    (Tier 2) URL 큐를 관리하고 정규식에 맞는 하위 링크를 계속 생성하는 생성기.
    """
    component_name = "WebCrawlGenerator"
    SUPPORTED_TYPES = ["web_crawl"]

    def initialize(
        self, 
        source: str, 
        link_pattern: str = ".*", 
        selectors: Optional[Dict[str, str]] = None,
        max_depth: int = 1,
        **kwargs
    ):
        self.start_url = source
        
        # 큐: (url, depth) 튜플 저장
        self.queue = deque()
        self.visited = set()
        
        # 초기 시드 추가
        self.queue.append((self.start_url, 0))
        self.visited.add(self.start_url)
        
        self.link_regex = re.compile(link_pattern)
        self.selectors = selectors or {}
        self.max_depth = max_depth
        
        self._log(f"Initialized WebCrawl. Seed: {source}, Pattern: {link_pattern}")

    def generate(self) -> Iterator[FetchTask]:
        """큐에 쌓인 작업을 하나씩 꺼내 파이프라인으로 보냄"""
        # 주의: 파이프라인 루프 구조상 여기서 계속 yield를 해줘야 함.
        # 큐가 비어있어도 feedback()에 의해 채워질 수 있으므로 즉시 종료하면 안 되지만,
        # 현재 파이프라인 구현(단일 루프)상 yield가 끝나면 종료됨.
        # 따라서 파이프라인 로직에 맞춰 큐가 빌 때까지 yield 함.
        
        while self.queue:
            url, depth = self.queue.popleft()
            
            task = FetchTask(
                source_type="http" if url.startswith("http") else "https",
                uri=url,
                # Selectors와 Depth 정보를 파람스로 전달
                params={
                    "selectors": self.selectors, 
                    "depth": depth
                }
            )
            yield task

    def feedback(self, result: FetchResult):
        """Fetcher 결과를 보고 다음 링크를 큐에 추가"""
        if not result.success or not result.data:
            return

        # 현재 작업의 깊이 확인
        current_depth = result.task.params.get("depth", 0)
        
        # 깊이 제한 도달 시 더 이상 링크 수집 안 함
        if current_depth >= self.max_depth:
            return

        # Fetcher가 찾아온 링크들 꺼내기
        found_links = result.data.get("__found_links__", [])
        
        added_count = 0
        for link in found_links:
            if link in self.visited:
                continue
            if self.link_regex.search(link):
                self.visited.add(link)
                self.queue.append((link, current_depth + 1))
                added_count += 1
        
        if added_count > 0:
            self._log(f"Feedback: Found {len(found_links)} links, Queued {added_count} new targets (Depth {current_depth+1})")