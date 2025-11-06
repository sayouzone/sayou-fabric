from abc import abstractmethod
from typing import Any
from sayou.core.base_component import BaseComponent
from sayou.loader.core.exceptions import WriterError

class BaseWriter(BaseComponent):
    """
    (Tier 1) '변환된 데이터'를 '영구 저장소'(e.g., File, DB)에
    '쓰는(Write)' 모든 Writer의 인터페이스. (Template Method)
    """
    component_name = "BaseWriter"
    
    def write(self, translated_data: Any):
        """
        [공통 골격] 쓰기 프로세스를 실행하고 로깅/예외처리를 수행합니다.
        Tier 2/3는 이 메서드를 오버라이드하지 않습니다.
        
        :param translated_data: Translator가 반환한 데이터
        """
        self._log(f"Writing data of type '{type(translated_data)}'...")
        try:
            # Tier 2/3가 '알맹이'를 구현
            self._do_write(translated_data)
            
            self._log(f"Write complete.")
        except Exception as e:
            self._log(f"Write failed: {e}")
            raise WriterError(f"Write failed: {e}")

    @abstractmethod
    def _do_write(self, translated_data: Any):
        """
        [구현 필수] 실제 쓰기 로직입니다.
        (e.g., file.write(), db_session.execute_batch())
        """
        raise NotImplementedError