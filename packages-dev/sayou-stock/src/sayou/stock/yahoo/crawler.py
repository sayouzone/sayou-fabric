from .client import YahooClient

from .parsers import (
    YahooAnalysisParser,
    YahooQuoteParser,
    YahooNewsParser,
    YahooChartParser,
    YahooFundamentalsParser,
)

class YahooCrawler:

    def __init__(self):
        self.client = YahooClient()

        # 파서 초기화
        self._analysis_parser = YahooAnalysisParser(self.client)
        self._quote_parser = YahooQuoteParser(self.client)
        self._news_parser = YahooNewsParser(self.client)
        self._chart_parser = YahooChartParser(self.client)
        self._fundamentals_parser = YahooFundamentalsParser(self.client)

    def info(self, ticker: str):
        return self._quote_parser.fetch(ticker)

    def calendar(self, ticker: str):
        """기업 캘린더 (Calendar) 조회"""
        return self._analysis_parser.fetch_calendar(ticker)

    def revenue_estimate(self, ticker: str):
        """기업 매출 추정치 (Revenue Estimate) 조회"""
        return self._analysis_parser.fetch_revenue_estimate(ticker)

    def earnings_estimate(self, ticker: str):
        """기업 이익 추정치 (Earning Estimate) 조회"""
        return self._analysis_parser.fetch_earnings_estimate(ticker)

    def eps_trend(self, ticker: str):
        """기업 EPS 추세 (EPS Trend) 조회"""
        return self._analysis_parser.fetch_eps_trend(ticker)

    def eps_revisions(self, ticker: str):
        """기업 EPS 수정치 (EPS Revisions) 조회"""
        return self._analysis_parser.fetch_eps_revisions(ticker)

    def news(self, query: str, max_articles: int = 100, period: str = "7"):
        return self._news_parser.fetch(query, max_articles, period)
    
    def chart(self, ticker: str, start_date: str | None = None, end_date: str | None = None):
        return self._chart_parser.fetch(ticker, start_date=start_date, end_date=end_date)

    def dividends(self, ticker: str):
        """기업 배당 (Dividends) 조회"""
        return self._chart_parser.dividends(ticker)

    def capital_gains(self, ticker: str):
        """기업 양도소득 (Capital Gains) 조회"""
        return self._chart_parser.capital_gains(ticker)

    def splits(self, ticker: str):
        """기업 주식 분할 (Splits) 조회"""
        return self._chart_parser.splits(ticker)
    
    def income_statement(self, ticker: str):
        """기업 손익계산서 (Income Statement) 조회"""
        return self._fundamentals_parser.fetch_financials(ticker, name="income", timescale="yearly")
    
    def quarterly_income_statement(self, ticker: str):
        """기업 손익계산서 (Income Statement) 조회 (분기)"""
        return self._fundamentals_parser.fetch_financials(ticker, name="income", timescale="quarterly")

    def balance_sheet(self, ticker: str):
        """기업 재무상태표 (Balance Sheet) 조회"""
        return self._fundamentals_parser.fetch_financials(ticker, name="balance-sheet", timescale="yearly")

    def quarterly_balance_sheet(self, ticker: str):
        """기업 재무상태표 (Balance Sheet) 조회 (분기)"""
        return self._fundamentals_parser.fetch_financials(ticker, name="balance-sheet", timescale="quarterly")

    def cash_flow(self, ticker: str):
        """기업 현금흐름 (Cash Flow) 조회"""
        return self._fundamentals_parser.fetch_financials(ticker, name="cash-flow", timescale="yearly")

    def quarterly_cash_flow(self, ticker: str):
        """기업 현금흐름 (Cash Flow) 조회 (분기)"""
        return self._fundamentals_parser.fetch_financials(ticker, name="cash-flow", timescale="quarterly")

    def earning_calendar(self, ticker: str):
        """기업 이익공시일 (Earning Calendar) 조회"""
        return self._quote_parser.fetch_earning_calendar(ticker, limit=100, offset=0)

    def recommendation(self, ticker: str):
        """기업 추천도움 (Recommendation) 조회"""
        return self._quote_parser.fetch_recommendation(ticker)

    def recommendation_summary(self, ticker: str):
        """기업 추천도움 (Recommendation) 조회"""
        return self._quote_parser.fetch_recommendation(ticker, as_dict=False)
