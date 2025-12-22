"""
Yahoo Crawler
===========================

Yahoo에서 주요 데이터를 추출하는 Python 패키지

Installation:
    pip install requests beautifulsoup4 lxml

Quick Start:
    >>> from yahoo import YahooCrawler
    >>> 
    >>> crawler = YahooCrawler()
    >>> 
    >>> # 기업 정보 조회
    >>> data = crawler.info(ticker)
    >>> print(f"기업 정보: {data}")
    >>> 
    >>> # 일별 시세 조회
    >>> start_date='2025-12-01'
    >>> end_date='2025-12-31'
    >>> data = crawler.market(ticker, start_date=start_date, end_date=end_date)
    >>> print(data)
    >>> 
    >>> # 배당 조회
    >>> ticker = "AAPL"
    >>> data = crawler.dividends(ticker=ticker)
    >>> print(data)
    >>> 
    >>> # Yahoo 뉴스 검색
    >>> print(f"\nYahoo 뉴스 검색: {ticker}")
    >>> data = crawler.news(query=ticker, max_articles=10)
    >>> print(data)
    >>> 
    >>> # Yahoo 재무제표
    >>> print(f"\nYahoo 재무제표 손익계산서 검색: {ticker}")
    >>> data = crawler.fundamentals(ticker)
    >>> print(data)
    >>> 
    >>> # Yahoo 재무제표 (분기)
    >>> print(f"\nYahoo 재무제표 손익계산서 (분기) 검색: {ticker}")
    >>> data = crawler.quarterly_fundamentals(ticker)
    >>> print(data)
    >>> 
    >>> # 재무상태표 (연간)
    >>> print(f"\nYahoo 재무제표 재무상태표 검색: {ticker}")
    >>> data = crawler.balance_sheet(ticker)
    >>> print(data)
    >>> 
    >>> # 재무상태표 (분기)
    >>> print(f"\nYahoo 재무제표 재무상태표 (분기) 검색: {ticker}")
    >>> data = crawler.quarterly_balance_sheet(ticker)
    >>> print(data)
    >>> 
    >>> # 현금흐름표 (연간)
    >>> print(f"\nYahoo 재무제표 현금흐름표 검색: {ticker}")
    >>> data = crawler.cash_flow(ticker)
    >>> print(data)
    >>> 
    >>> # 현금흐름표 (분기)
    >>> print(f"\nYahoo 재무제표 현금흐름표 (분기) 검색: {ticker}")
    >>> data = crawler.quarterly_cash_flow(ticker)
    >>> print(data)

Supported Cases:
    - 기업 정보 조회
    - 일별 시세 조회
    - 배당 조회
    - 뉴스 조회
    - 재무제표 조회

Note:
    Yahoo에서 User-Agent를 사용하세요.
"""

__version__ = "0.1.0"
__author__ = "SeongJung Kim"

from .crawler import YahooCrawler
from .client import YahooClient
#from .models import (
    # 공통
    #DartConfig,
#)

from .parsers import (
    YahooAnalysisParser,
    YahooQuoteParser,
    YahooChartParser,
    YahooNewsParser,
    YahooFundamentalsParser,
)

__all__ = [
    # 메인 클래스
    "YahooCrawler",
    "YahooClient",
    
    # 데이터 모델
    #"DartConfig",
    
    # 파서
    "YahooAnalysisParser",
    "YahooQuoteParser",
    "YahooChartParser",
    "YahooNewsParser",
    "YahooFundamentalsParser",
]
