from abc import abstractmethod
from typing import Any, Dict

from sayou.core.base_component import BaseComponent

from ..core.exceptions import WrapperError 
from ..schemas.sayou_standard import WrapperOutput

class BaseAdapter(BaseComponent):
    """
    (Tier 1) 외부 데이터를 Sayou 표준 규격으로 변환(Adapt)하는 인터페이스.
    약속: 구현체는 'adapter' 폴더에 위치해야 합니다.
    """
    component_name = "BaseAdapter"

    def adapt(self, raw_data: Any) -> Dict[str, Any]:
        """
        [Public API] 데이터를 받아 표준 규격(Dict)으로 반환합니다.
        """
        self._log(f"Starting adaptation process...")
        try:
            # 1. 실제 변환 로직 수행 (Tier 2/3)
            output_model = self._do_adapt(raw_data)
            
            # 2. Pydantic 모델을 Dict로 변환 (Pipeline 호환성)
            return output_model.model_dump()
            
        except Exception as e:
            raise WrapperError(f"Adaptation failed in {self.component_name}: {e}")

    @abstractmethod
    def _do_adapt(self, raw_data: Any) -> WrapperOutput:
        """
        [구현 필수] Raw Data를 받아 WrapperOutput 객체를 반환해야 합니다.
        """
        raise NotImplementedError