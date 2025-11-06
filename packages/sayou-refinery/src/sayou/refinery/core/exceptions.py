from sayou.core.exceptions import SayouCoreError

class RefineryError(SayouCoreError):
    """Refinery 컴포넌트 관련 기본 오류"""
    pass

class InterfaceError(SayouCoreError):
    """인터페이스 계약 관련 오류"""
    pass
    
class PatternError(SayouCoreError):
    """Tier 2 일반 엔진(Pattern) 관련 오류 (사용 안 함)"""
    pass

class PluginError(SayouCoreError):
    """Tier 3 플러그인 관련 오류"""
    pass