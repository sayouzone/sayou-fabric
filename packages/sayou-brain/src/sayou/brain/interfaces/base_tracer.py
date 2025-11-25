from abc import abstractmethod
from typing import Dict, Any

from sayou.core.base_component import BaseComponent

from ..core.exceptions import BrainError

class BaseTracer(BaseComponent):
    component_name = "BaseTracer"

    def trace(self, route_result: Dict[str, Any]) -> Dict[str, Any]:
        """[공통 골격] 라우팅 결과(도메인)를 기반으로 데이터 위치를 추적합니다."""
        domain = route_result.get("domain", "unknown")
        self._log(f"Tracing data location for domain: '{domain}'")
        try:
            trace_result = self._do_trace(route_result)
            
            if "source_type" not in trace_result:
                raise BrainError("Trace result must contain 'source_type'.")
                
            self._log(f"Data location found: {trace_result}")
            return trace_result
        except Exception as e:
            raise BrainError(f"Data tracing failed: {e}")

    @abstractmethod
    def _do_trace(self, route_result: Dict[str, Any]) -> Dict[str, Any]:
        """[T2 구현 필수] (e.g., KG(Extractor) 쿼리)
        (결과 포맷: {"source_type": "vector_db", "index_name": "user_profiles", ...})
        """
        raise NotImplementedError