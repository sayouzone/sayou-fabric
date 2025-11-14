from abc import abstractmethod
from typing import List
from sayou.core.base_component import BaseComponent

class BaseConverter(BaseComponent):
    """
    (Tier 1) 파일 변환기 인터페이스 (e.g., HWP -> PDF).
    """
    component_name = "BaseConverter"
    SUPPORTED_TYPES: List[str] = []

    def convert(self, file_bytes: bytes, file_name: str, **kwargs) -> bytes:
        """
        [공통 뼈대] 변환 실행 및 에러 핸들링
        """
        self._log(f"Converting file: {file_name}...")
        try:
            converted_bytes = self._do_convert(file_bytes, file_name, **kwargs)
            if not converted_bytes:
                raise ValueError("Converter returned empty bytes.")
            
            self._log(f"Conversion successful. ({len(converted_bytes)} bytes)")
            return converted_bytes
            
        except Exception as e:
            self._log(f"Conversion failed for {file_name}: {e}", level="error")
            return None

    @abstractmethod
    def _do_convert(self, file_bytes: bytes, file_name: str, **kwargs) -> bytes:
        """[구현 필수] 실제 변환 로직 (e.g., LibreOffice 호출)"""
        raise NotImplementedError