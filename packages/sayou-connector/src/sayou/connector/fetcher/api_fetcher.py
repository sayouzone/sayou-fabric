from typing import Any, Dict
from ..interfaces.base_fetcher import BaseFetcher
import requests

class ApiFetcher(BaseFetcher):
    """
    (Tier 2) 'HTTP API'에서 데이터를 가져오는 일반 엔진.
    BaseFetcher(Tier 1)의 '_do_fetch'를 구현합니다.
    """
    component_name = "ApiFetcher"

    def initialize(self, **kwargs):
        
        # --- [탐정 코드 1] ---
        print("\n[DEBUG] 1. ApiFetcher.initialize() 시작.")
        
        try:
            super().initialize(**kwargs) 
        except Exception as e:
            print(f"[DEBUG] 1-ERROR. super().initialize() 실패: {e}")
            raise e
            
        # --- [탐정 코드 2] ---
        print(f"[DEBUG] 2. super() 실행 완료. (self._log 존재 여부: {hasattr(self, '_log')})")

        self.timeout = kwargs.get("timeout", 10) 
        self.headers = kwargs.get("headers", {"User-Agent": "Sayou-Connector/0.0.1"})
        
        # --- [탐정 코드 3] ---
        print("[DEBUG] 3. _session 생성 *직전*.")
        
        self._session = requests.Session()
        self._session.headers.update(self.headers)
        
        # --- [탐정 코드 4] ---
        print("[DEBUG] 4. _session 생성 *직후*. (self._session 존재 여부: {hasattr(self, '_session')})")
        
        self._log("ApiFetcher initialized correctly (session created).")
        
        # --- [탐정 코드 5] ---
        print("[DEBUG] 5. ApiFetcher.initialize() 종료.\n")

    def _do_fetch(self, target: str, query: Dict[str, Any]) -> Any:
        """
        Tier 1의 'fetch()'가 호출할 '알맹이' 로직입니다.
        """
        # 'query' 딕셔너리에서 RAG 예제가 보낸 'url_paths'를 추출
        url_paths_list = query.get('url_paths')
        
        if url_paths_list is None:
            raise ValueError("ApiFetcher 'query' must contain 'url_paths' key for Seoul API.")
            
        try:
            url = target
            if "url_paths" in query:
                url += "/" + "/".join(map(str, query["url_paths"]))
            api_params = query.get("api_params", {})
            response = self._session.get(url, params=api_params, timeout=self.timeout)
            
            response.raise_for_status() # 4xx, 5xx 에러 시 예외 발생
            return response.text
            
        except Exception as e:
            # 이 에러는 BaseFetcher.fetch()의 except 블록으로 전달됩니다.
            self._log(f"ApiFetcher _do_fetch failed: {e}")
            raise e # 예외를 다시 발생시켜 BaseFetcher.fetch()가 잡도록 함