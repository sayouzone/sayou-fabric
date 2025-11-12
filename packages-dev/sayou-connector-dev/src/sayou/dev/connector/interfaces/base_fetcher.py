from abc import abstractmethod
from typing import Any, Dict
from sayou.core.base_component import BaseComponent
from ..core.exceptions import ConnectorError

class BaseFetcher(BaseComponent):
    """
    (Tier 1) "무엇을" 가져올지 정의하는 모든 Fetcher의 인터페이스.
    (e.g., HTTP GET, DB SELECT, S3 GetObject)
    
    이 클래스는 '실행 골격(fetch)'을 제공합니다. (Template Method)
    """
    component_name = "BaseFetcher"

    def fetch(self, target: str, query: Dict[str, Any] = None) -> Any:
        """
        [공통 골격] 'target' 리소스에 'query'를 실행하여 데이터를 가져옵니다.
        Tier 2/3는 이 메서드를 오버라이드하지 않습니다.
        
        :param target: 리소스 (e.g., 기본 URL, DB 테이블, 파일 경로)
        :param query: (선택적) 실행할 쿼리/명령
                    (e.g., {'columns': ['name']}, {'api_params': {...}})
                    If None, "전체"를 의미합니다.
        :return: Raw Data (bytes, str, dict, list)
        """
        self._log(f"Fetching from target '{target}' with query '{query}'...")
        try:
            # Tier 2/3가 '알맹이'를 구현
            if query is None:
                query = {} # None 대신 빈 dict 전달
                
            data = self._do_fetch(target, query)
            return data
            
        except Exception as e:
            self._log(f"Fetch failed for {target}: {e}")
            return None # 실패 시 None 반환

    @abstractmethod
    def _do_fetch(self, target: str, query: Dict[str, Any]) -> Any:
        """
        [구현 필수] 실제 Fetch 로직입니다.
        'query' 딕셔너리를 파싱하여 'SELECT *'가 아닌 'SELECT name'을 수행합니다.
        """
        raise NotImplementedError