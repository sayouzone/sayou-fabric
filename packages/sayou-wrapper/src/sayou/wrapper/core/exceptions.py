# src/sayou/wrapper/core/exceptions.py
from sayou.core.exceptions import SayouCoreError

class WrapperError(SayouCoreError):
    """'sayou-wrapper' 툴킷의 모든 오류가 상속받는 베이스 예외"""
    pass

class MappingError(WrapperError):
    """'Mapper' (Tier 1/2/3) 실행 중 발생하는 오류"""
    pass

class ValidationError(WrapperError):
    """'Validator' (Tier 1/2/3) 실행 중 발생하는 오류 (e.g., 스키마 위반)"""
    pass