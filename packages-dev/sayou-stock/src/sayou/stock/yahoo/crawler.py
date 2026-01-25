# Copyright (c) 2025, Sayouzone
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
 
from .client import YahooClient

from .parsers import (
    YahooAnalysisParser,
    YahooQuoteParser,
    YahooNewsParser,
    YahooChartParser,
    YahooFundamentalsParser,
    YahooHoldersParser,
    YahooSummaryParser,
)

class YahooCrawler:

    def __init__(self):
        self.client = YahooClient()

        # 파서 초기화
        self._analysis_parser: Optional[YahooAnalysisParser] = None
        self._quote_parser: Optional[YahooQuoteParser] = None
        self._news_parser: Optional[YahooNewsParser] = None
        self._chart_parser: Optional[YahooChartParser] = None
        self._fundamentals_parser: Optional[YahooFundamentalsParser] = None
        self._holders_parser: Optional[YahooHoldersParser] = None
        self._summary_parser: Optional[YahooSummaryParser] = None

    @property
    def analysis_parser(self) -> YahooAnalysisParser:
        """Lazy initialization of analysis parser"""
        if self._analysis_parser is None:
            self._analysis_parser = YahooAnalysisParser(self.client)
        return self._analysis_parser

    @property
    def news_parser(self) -> YahooNewsParser:
        """Lazy initialization of news parser"""
        if self._news_parser is None:
            self._news_parser = YahooNewsParser(self.client)
        return self._news_parser

    @property
    def quote_parser(self) -> YahooQuoteParser:
        """Lazy initialization of quote parser"""
        if self._quote_parser is None:
            self._quote_parser = YahooQuoteParser(self.client)
        return self._quote_parser

    @property
    def chart_parser(self) -> YahooChartParser:
        """Lazy initialization of chart parser"""
        if self._chart_parser is None:
            self._chart_parser = YahooChartParser(self.client)
        return self._chart_parser

    @property
    def fundamentals_parser(self) -> YahooFundamentalsParser:
        """Lazy initialization of fundamentals parser"""
        if self._fundamentals_parser is None:
            self._fundamentals_parser = YahooFundamentalsParser(self.client)
        return self._fundamentals_parser

    @property
    def holders_parser(self) -> YahooHoldersParser:
        """Lazy initialization of holders parser"""
        if self._holders_parser is None:
            self._holders_parser = YahooHoldersParser(self.client)
        return self._holders_parser

    @property
    def summary_parser(self) -> YahooSummaryParser:
        """Lazy initialization of summary parser"""
        if self._summary_parser is None:
            self._summary_parser = YahooSummaryParser(self.client)
        return self._summary_parser

    def calendar(self, ticker: str):
        """기업 캘린더 (Calendar) 조회"""
        return self.analysis_parser.fetch_calendar(ticker)

    def revenue_estimate(self, ticker: str):
        """기업 매출 추정치 (Revenue Estimate) 조회"""
        return self.analysis_parser.fetch_revenue_estimate(ticker)

    def earnings_estimate(self, ticker: str):
        """기업 수익 추정치 (Earning Estimate) 조회"""
        return self.analysis_parser.fetch_earnings_estimate(ticker)

    def earnings_history(self, ticker: str):
        """기업 수익 내역 (Earnings History) 조회"""
        return self.analysis_parser.fetch_earnings_history(ticker)

    def eps_trend(self, ticker: str):
        """기업 EPS 추세 (EPS Trend) 조회"""
        return self.analysis_parser.fetch_eps_trend(ticker)

    def growth_estimate(self, ticker: str):
        """기업 성장 추정치 (Growth Estimate) 조회"""
        return self.analysis_parser.fetch_growth_estimate(ticker)

    def eps_revisions(self, ticker: str):
        """기업 EPS 수정치 (EPS Revisions) 조회"""
        return self.analysis_parser.fetch_eps_revisions(ticker)

    def news(self, query: str, max_articles: int = 100, period: str = "7"):
        return self.news_parser.fetch(query, max_articles, period)
    
    def chart(self, ticker: str, start_date: str | None = None, end_date: str | None = None):
        """기업 차트 (Chart) 조회 (yf.Ticker.history)"""
        return self.chart_parser.fetch(ticker, start_date=start_date, end_date=end_date)

    def dividends(self, ticker: str):
        """기업 배당 (Dividends) 조회"""
        return self.chart_parser.dividends(ticker)

    def capital_gains(self, ticker: str):
        """기업 양도소득 (Capital Gains) 조회"""
        return self.chart_parser.capital_gains(ticker)

    def splits(self, ticker: str):
        """기업 주식 분할 (Splits) 조회"""
        return self.chart_parser.splits(ticker)
    
    def income_statement(self, ticker: str):
        """기업 손익계산서 (Income Statement) 조회"""
        return self.fundamentals_parser.fetch_financials(ticker, name="income", timescale="yearly")
    
    def quarterly_income_statement(self, ticker: str):
        """기업 손익계산서 (Income Statement) 조회 (분기)"""
        return self.fundamentals_parser.fetch_financials(ticker, name="income", timescale="quarterly")

    def balance_sheet(self, ticker: str):
        """기업 재무상태표 (Balance Sheet) 조회"""
        return self.fundamentals_parser.fetch_financials(ticker, name="balance-sheet", timescale="yearly")

    def quarterly_balance_sheet(self, ticker: str):
        """기업 재무상태표 (Balance Sheet) 조회 (분기)"""
        return self.fundamentals_parser.fetch_financials(ticker, name="balance-sheet", timescale="quarterly")

    def cash_flow(self, ticker: str):
        """기업 현금흐름 (Cash Flow) 조회"""
        return self.fundamentals_parser.fetch_financials(ticker, name="cash-flow", timescale="yearly")

    def quarterly_cash_flow(self, ticker: str):
        """기업 현금흐름 (Cash Flow) 조회 (분기)"""
        return self.fundamentals_parser.fetch_financials(ticker, name="cash-flow", timescale="quarterly")

    def summary(self, ticker: str):
        """기업 요약 정보 (Summary) 조회"""
        return self.summary_parser.fetch_summary(ticker)

    def holders(self, ticker: str):
        """기업 소유주 (Holders) 조회"""
        return self.holders_parser.fetch_holders(ticker)

    def earning_calendar(self, ticker: str):
        """기업 이익공시일 (Earning Calendar) 조회"""
        return self.quote_parser.fetch_earning_calendar(ticker, limit=100, offset=0)

    def sec_filings(self, ticker: str):
        """기업 SEC 공시 정보 (SEC Filings) 조회"""
        return self.quote_parser.fetch_sec_filings(ticker)

    def recommendation(self, ticker: str):
        """기업 추천도움 (Recommendation) 조회"""
        return self.quote_parser.fetch_recommendation(ticker)

    def recommendation_summary(self, ticker: str):
        """기업 추천도움 (Recommendation) 조회"""
        return self.quote_parser.fetch_recommendation(ticker, as_dict=False)
