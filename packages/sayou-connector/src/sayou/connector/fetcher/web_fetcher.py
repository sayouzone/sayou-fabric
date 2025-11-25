import requests
from urllib.parse import urljoin
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from ..core.models import FetchTask, FetchResult
from ..interfaces.base_fetcher import BaseFetcher

class SimpleWebFetcher(BaseFetcher):
    """
    (Tier 2) 정적 웹 페이지를 수집하고, 데이터와 하위 링크를 추출합니다.
    """
    component_name = "SimpleWebFetcher"
    SUPPORTED_TYPES = ["http", "https"]

    def fetch(self, task: FetchTask) -> FetchResult:
        if not BeautifulSoup:
            return FetchResult(task, None, False, "BeautifulSoup4 not installed.")

        try:
            url = task.uri
            headers = {"User-Agent": "Sayou-Connector/0.0.1"}
            
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, "html.parser")

            # 1. 데이터 추출 (선택자가 없으면 빈 딕셔너리)
            selectors = task.params.get("selectors", {})
            extracted_data = {}
            
            if selectors:
                for key, selector in selectors.items():
                    elements = soup.select(selector)
                    if elements:
                        extracted_data[key] = "\n".join([e.get_text(strip=True) for e in elements])
            
            # 선택자가 있어도 매칭 안 되면 원본 HTML 일부 저장
            if not extracted_data:
                extracted_data["_raw_preview"] = resp.text[:200]

            # 2. 다음 링크 후보 추출
            found_links = set() # 중복 제거를 위해 Set 사용
            for a_tag in soup.find_all("a", href=True):
                # 상대 경로를 절대 경로로 변환
                absolute_link = urljoin(url, a_tag["href"])
                # 간단한 필터링 (http로 시작하는 것만)
                if absolute_link.startswith("http"):
                    found_links.add(absolute_link)

            # 링크 정보를 data 딕셔너리에 '반드시' 포함시킨 후 리턴
            extracted_data["__found_links__"] = list(found_links)

            return FetchResult(
                task=task,
                data=extracted_data, # 여기에 __found_links__가 들어있음
                success=True
            )

        except Exception as e:
            return FetchResult(task=task, data=None, success=False, error=str(e))