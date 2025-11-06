from sayou.core.exceptions import SayouCoreError

class AssemblerError(SayouCoreError):
    """Assembler 컴포넌트 관련 기본 오류"""
    pass

class SchemaError(SayouCoreError):
    """온톨로지 스키마 로딩 또는 검증 관련 오류"""
    pass
    
class BuildError(SayouCoreError):
    """데이터 구축(Build) 단계 관련 오류"""
    pass

class StoreError(SayouCoreError):
    """데이터 저장(Store) 단계 관련 오류"""
    pass