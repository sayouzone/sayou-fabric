from abc import abstractmethod
from typing import List
from sayou.core.base_component import BaseComponent
from ..core.exceptions import ConnectorError

class BaseSeeder(BaseComponent):
    """
    (Tier 1) "어디서" 수집을 시작할지 Seed 리스트(e.g., URL, 쿼리)를
    생성하는 모든 Seeder의 인터페이스.
    
    이 클래스는 '실행 골격(seed)'을 제공합니다. (Template Method)
    """
    component_name = "BaseSeeder"

    def seed(self) -> List[str]:
        """
        [공통 골격] Seeding 프로세스를 실행하고 로깅/예외처리를 수행합니다.
        Tier 2/3는 이 메서드를 오버라이드하지 않습니다.
        """
        self._log("Seeding process started...")
        try:
            # Tier 2/3가 '알맹이'를 구현
            seed_list = self._do_seed()
            
            self._log(f"Generated {len(seed_list)} seeds.")
            return seed_list
        except Exception as e:
            self._log(f"Seeding failed: {e}")
            raise ConnectorError(f"Seeding failed: {e}")

    @abstractmethod
    def _do_seed(self) -> List[str]:
        """
        [구현 필수] 실제 Seed 생성 로직입니다.
        (e.g., 파일 읽기, DB 쿼리, 고정 리스트 반환)
        """
        raise NotImplementedError