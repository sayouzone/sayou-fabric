from abc import abstractmethod
from typing import Any

from sayou.core.base_component import BaseComponent

from ..core.exceptions import WriterError

class BaseWriter(BaseComponent):
    """
    (Tier 1) 데이터를 목적지에 적재하는 모든 Writer의 인터페이스.
    Template Method 패턴을 사용하여 로깅과 예외 처리를 강제합니다.
    """
    component_name = "BaseWriter"
    SUPPORTED_TYPES = [] 

    def write(self, data: Any, destination: str, **kwargs) -> bool:
        """
        [공통 골격] 적재 프로세스를 제어합니다. (Override 금지 권장)
        """
        self._log(f"Starting write to '{destination}' (Type: {type(data).__name__})...")
        
        try:
            # Pre-check logic (옵션)
            if not data:
                self._log("Data is empty. Skipping write.")
                return False

            # Tier 2/3의 실제 구현 호출
            result = self._do_write(data, destination, **kwargs)
            
            if result:
                self._log("Write completed successfully.")
            else:
                self._log("Write completed but returned False.")
            
            return result

        except Exception as e:
            self._log(f"Wite failed: {e}")
            # 여기서 에러를 삼킬지, 다시 던질지는 정책 결정
            # 파이프라인의 중단을 막으려면 False 반환, 멈추려면 raise
            return False 

    @abstractmethod
    def _do_write(self, data: Any, destination: str, **kwargs) -> bool:
        """
        [구현 필수] 실제 적재 로직을 구현하세요.
        성공 시 True, 실패 시 False를 반환하세요.
        """
        raise NotImplementedError