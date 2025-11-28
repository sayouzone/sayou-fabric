import logging

from abc import ABC

class BaseComponent(ABC):
    """
    '사유존' 툴킷의 모든 컴포넌트가 상속받는 최상위 추상 베이스 클래스.
    Python 표준 logging 모듈을 통합하여 일관된 로그 관리를 지원합니다.
    """
    component_name: str = "BaseComponent"

    def __init__(self):
        self.logger = logging.getLogger(self.component_name)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s [%(name)s] %(levelname)s: %(message)s', 
                datefmt='%H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def initialize(self, **kwargs):
        """
        (선택적) 초기화 시 필요한 설정 또는 상태 등록.
        """
        pass 

    def _log(self, msg: str, level: str = "info"):
        if level.lower() == "debug":
            self.logger.debug(msg)
        elif level.lower() == "warning":
            self.logger.warning(msg)
        elif level.lower() == "error":
            self.logger.error(msg)
        else:
            self.logger.info(msg)

    def __repr__(self):
        return f"<{self.component_name}>"