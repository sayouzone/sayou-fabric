class SayouCoreError(Exception):
    """
    '사유존' 툴킷 생태계의 모든 커스텀 오류가 상속받는
    최상위 베이스 예외 클래스.
    
    사용자는 'except SayouCoreError:' 한 줄로
    모든 사유존 관련 예외를 처리할 수 있습니다.
    """
    pass

class InitializationError(SayouCoreError):
    """'initialize()' 메서드 실패 시 발생하는 공통 오류"""
    pass