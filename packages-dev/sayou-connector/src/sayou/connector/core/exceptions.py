from sayou.core.exceptions import SayouCoreError

class InitializationError(SayouCoreError):
    """'initialize()' 메서드 실패 시 발생하는 공통 오류"""
    pass

class ConnectorError(SayouCoreError):
    """'sayou-connector' 툴킷의 모든 오류가 상속받는 베이스 예외"""
    pass

class SeederError(ConnectorError):
    """Tier 1/2/3 'Seeder' 실행 중 발생하는 오류"""
    pass

class FetcherError(ConnectorError):
    """Tier 1/2/3 'Fetcher' 실행 중 발생하는 오류 (e.g., HTTP 404, DB 연결 실패)"""
    pass

class GeneratorError(ConnectorError):
    """Tier 1/2/3 'Generator' 실행 중 발생하는 오류 (e.g., HTML 파싱 실패)"""
    pass