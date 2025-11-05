from abc import ABC

class BaseComponent(ABC):
    """
    (Tier 0) '사유존' 툴킷의 모든 컴포넌트가 상속받는
    최상위 추상 베이스 클래스.
    """
    component_name: str = "BaseComponent"

    def initialize(self, **kwargs):
        """
        (선택적) 초기화 시 필요한 설정 또는 상태 등록.
        필요한 컴포넌트만 이 메서드를 오버라이드합니다.
        """
        pass 

    def _log(self, msg: str):
        """
        컴포넌트 실행 로그를 표준화된 포맷으로 출력합니다.
        (v.0.0.1 에서는 print, v.1.0.0 에서는 logging 모듈로 교체)
        """
        print(f"[{self.component_name}] {msg}")

    def __repr__(self):
        return f"<{self.component_name}>"