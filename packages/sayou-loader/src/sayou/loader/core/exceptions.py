from sayou.core.exceptions import SayouCoreError

class InitializationError(SayouCoreError):
    """'initialize()' 메서드 실패 시 발생하는 공통 오류"""
    pass

class LoaderError(SayouCoreError):
    """'sayou-loader' 툴킷의 모든 오류가 상속받는 베이스 예외"""
    pass

class TranslationError(LoaderError):
    """'Translator' (Tier 1/2/3) 실행 중 발생하는 오류 (e.g., KG -> Cypher 변환 실패)"""
    pass

class WriterError(LoaderError):
    """'Writer' (Tier 1/2/3) 실행 중 발생하는 오류 (e.g., DB 연결 실패, I/O 실패)"""
    pass