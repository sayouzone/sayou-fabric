from abc import abstractmethod
from typing import List, Any
from sayou.core.base_component import BaseComponent

class BaseGenerator(BaseComponent):
    """
    (Tier 1) "더(More)" 수집할 대상을 탐색하는 모든 Generator의 인터페이스.
    (e.g., HTML에서 <a> 태그 찾기, API 응답에서 'next_page' URL 찾기)
    """
    component_name = "BaseGenerator"

    def generate(self, raw_data: Any) -> List[str]:
        """[공통 골격] Fetch된 데이터에서 다음 Seed 리스트를 생성합니다."""
        try:
            # Tier 2/3가 '알맹이'를 구현
            return self._do_generate(raw_data)
        except Exception as e:
            self._log(f"Failed to generate new seeds: {e}")
            return [] # 생성 실패 시 빈 리스트 반환

    @abstractmethod
    def _do_generate(self, raw_data: Any) -> List[str]:
        """
        [구현 필수] 실제 Gerenate 로직입니다.
        (e.g., <a> 태그 파싱, 'next_page_token' 파싱)
        """
        raise NotImplementedError