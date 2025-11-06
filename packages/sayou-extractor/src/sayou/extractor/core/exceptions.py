from sayou.core.exceptions import SayouCoreError

class ExtractorError(SayouCoreError):
    """'sayou-extractor' 툴킷의 모든 오류가 상속받는 베이스 예외"""
    pass

class RetrievalError(ExtractorError): # 👈 [신규] Retriever 전용 예외
    """'Retriever' (Tier 1/2/3) 실행 중 발생하는 오류"""
    pass

class QueryError(ExtractorError): # 👈 [신규] Querier 전용 예외
    """'Querier' (Tier 1/2/3)가 쿼리를 실행하는 중 발생하는 오류"""
    pass

class SearchError(ExtractorError): # 👈 [신규] Searcher 전용 예외
    """'Searcher' (Tier 1/2/3)가 검색을 실행하는 중 발생하는 오류"""
    pass