from typing import Any, Dict
from ..interfaces.base_fetcher import BaseFetcher
import requests

class ApiFetcher(BaseFetcher):
    """
    (Tier 2) 'HTTP API'에서 'params' 또는 'path'를 사용하여 
    데이터를 가져오는 일반 엔진.
    """
    component_name = "ApiFetcher"
    
    def initialize(self, **kwargs):
        self.timeout = kwargs.get("timeout", 10)
        self.headers = kwargs.get("headers", {"User-Agent": "Sayou-Connector/0.0.1"})
        self._session = requests.Session()
        self._session.headers.update(self.headers)

    def _do_fetch(self, target: str, query: Dict[str, Any]) -> Any:
        # target = Base URL (e.g., "http://openapi.seoul.go.kr:8088/KEY/json/getShtrmPath")
        # query = {'url_paths': ['1', '100', '마곡', '강남', '2025-10-31 10:00:00'],
        #          'api_params': {'type': 'transfer'}} (가정)
        
        # 1. URL Path 조립 (e.g., .../마곡/강남)
        url = target
        if "url_paths" in query:
            url += "/" + "/".join(map(str, query["url_paths"]))
            
        # 2. Query Parameter 조립 (e.g., ?type=transfer)
        api_params = query.get("api_params", {})
        
        # ⭐️ 'query'를 사용하여 "멍청하지 않은" 요청 생성
        response = self._session.get(url, params=api_params, timeout=self.timeout)
        response.raise_for_status() # 4xx/5xx 에러 시 예외 발생
        
        # (JSON 문자열 반환. 파싱은 Wrapping의 몫)
        return response.text