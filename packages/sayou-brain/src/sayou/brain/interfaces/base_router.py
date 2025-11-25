from abc import abstractmethod
from typing import Dict, Any, List

from sayou.core.base_component import BaseComponent

from ..core.exceptions import BrainError

class BaseRouter(BaseComponent):
    component_name = "BaseRouter"

    def route(self, query: str, chat_history: List = None) -> Dict[str, Any]:
        """[공통 골격] 쿼리 라우팅을 실행하고 결과를 검증합니다."""
        self._log(f"Routing query: '{query[:30]}...'")
        try:
            route_result = self._do_route(query, chat_history or [])
            
            if "domain" not in route_result or "confidence" not in route_result:
                raise BrainError("Route result must contain 'domain' and 'confidence'.")
                
            self._log(f"Route result: {route_result}")
            return route_result
        except Exception as e:
            raise BrainError(f"Routing failed: {e}")

    @abstractmethod
    def _do_route(self, query: str, chat_history: List) -> Dict[str, Any]:
        """[T2 구현 필수] (e.g., SFT 호출, 키워드 매칭)
        (결과 포맷: {"domain": "user_profile", "confidence": 0.9, ...})
        """
        raise NotImplementedError