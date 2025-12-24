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
 
import logging
import pandas as pd

from datetime import datetime, timedelta
from typing import Any, Literal, Optional

from ..client import YahooClient
from ..utils import (
    _QUERY2_URL_,
    _QUOTE_SUMMARY_URL_,
    _QUOTE_URL_,
    _CRUMB_URL_,
    quote_summary_valid_modules
)

from .quote import YahooQuoteParser

logger = logging.getLogger(__name__)

class YahooAnalysisParser:
    """
    Yahoo Finance 분석 데이터 파서
    
    - Calendar Events (배당/실적 발표 일정)
    - Earnings Trends (EPS/매출 추정치)
    
    References:
        https://github.com/ranaroussi/yfinance/blob/main/yfinance/scrapers/analysis.py
    """

    TREND_KEYS = Literal["earningsEstimate", "revenueEstimate", "epsTrend", "epsRevisions"]

    MODULES = [
        "financialData",
        "quoteType", 
        "defaultKeyStatistics",
        "assetProfile",
        "summaryDetail",
    ]

    def __init__(self, client: YahooClient):
        self.client = client
        self._crumb: Optional[str] = None

        self.quote_parser = YahooQuoteParser(self.client)

    def fetch_calendar(self, ticker: str):
        """
        배당/실적 발표 일정 조회
        
        Args:
            ticker: 종목 심볼
        
        Returns:
            {
                'Dividend Date': date,
                'Ex-Dividend Date': date,
                'Earnings Date': [date, ...],
                'Earnings High': float,
                'Earnings Low': float,
                'Earnings Average': float,
                'Revenue High': int,
                'Revenue Low': int,
                'Revenue Average': int,
            }
        """
        result = self.quote_parser.fetch_quote(ticker, modules=["calendarEvents"])
        events = self._extract_module(result, "calendarEvents")

        if not events:
            return {}

        calendar = {}

        # 배당 일정
        if 'dividendDate' in events:
            calendar['Dividend Date'] = self._timestamp_to_date(events.get('dividendDate', 0))
        if 'exDividendDate' in events:
            calendar['Ex-Dividend Date'] = self._timestamp_to_date(events.get('exDividendDate', 0))
        
        # 실적 발표 일정
        earnings = events.get('earnings', {})
        if 'earningsDate' in earnings:
            calendar['Earnings Date'] = [self._timestamp_to_date(ts) for ts in earnings.get('earningsDate', [])]
            calendar['Earnings High'] = earnings.get('earningsHigh', None)
            calendar['Earnings Low'] = earnings.get('earningsLow', None)
            calendar['Earnings Average'] = earnings.get('earningsAverage', None)
            calendar['Revenue High'] = earnings.get('revenueHigh', None)
            calendar['Revenue Low'] = earnings.get('revenueLow', None)
            calendar['Revenue Average'] = earnings.get('revenueAverage', None)
        
        return calendar

    def fetch_calendar_as_dataframe(self, ticker: str) -> pd.DataFrame:
        """배당/실적 발표 일정을 DataFrame으로 반환"""
        calendar = self.fetch_calendar(ticker)
        
        if not calendar:
            return pd.DataFrame()
        
        # Earnings Date 리스트 처리
        if "Earnings Date" in calendar:
            dates = calendar["Earnings Date"]
            calendar["Earnings Date"] = dates[0] if dates else None
            if len(dates) > 1:
                calendar["Earnings Date End"] = dates[-1]
        
        return pd.DataFrame([calendar])

    # ==================== Earnings Trends ====================

    def fetch_earnings_estimate(self, ticker: str):
        """이익 추정치 (Earnings Estimate)"""
        return self._fetch_earning_trend(ticker, "earningsEstimate")

    def fetch_revenue_estimate(self, ticker: str):
        """매출 추정치 (Revenue Estimate)"""
        return self._fetch_earning_trend(ticker, "revenueEstimate")

    def fetch_earnings_history(self, ticker: str):
        """이익 추이 (Earnings History)"""
        return self._fetch_earning_history(ticker, "earningsHistory")

    def fetch_eps_trend(self, ticker: str):
        """EPS 추세 (EPS Trend)"""
        return self._fetch_earning_trend(ticker, "epsTrend")

    def fetch_eps_revisions(self, ticker: str):
        """EPS 수정치 (EPS Revisions)"""
        return self._fetch_earning_trend(ticker, "epsRevisions")

    def fetch_growth_estimate(self, ticker: str):
        """성장 추정치 (Growth Estimate)"""

        # Ticker 성장 추정치
        result = self.quote_parser.fetch_quote(ticker, modules=['earningsTrend'])
        earnings_trend = self._extract_module(result, "earningsTrend").get('trend', {})

        data = []
        for item in earnings_trend:
            period = item.get("period", {})
            row = {
                "period": period,
                ticker: item.get("growth", {}).get("raw", None),
            }
            data.append(row)

        # Industry 성장 추정치
        modules = ['industryTrend', 'sectorTrend', 'indexTrend']
        result = self.quote_parser.fetch_quote(ticker, modules=modules)
        trends = result.get('quoteSummary', {}).get('result', [{}])[0]
        #print(trends)

        if not trends:
            df = pd.DataFrame(data).set_index("period").dropna(how='all')
            return df

        for trend_name, trend_info in trends.items():
            if trend_info.get("estimates"):
                symbol = trend_info.get("symbol")
                for estimate in trend_info.get("estimates"):
                    period = estimate.get("period", {})
                    existing_row = next((row for row in data if row.get("period") == period), None)
                    if existing_row:
                        #existing_row[trend_name] = estimate.get("growth", {})
                        existing_row[symbol] = estimate.get("growth", {})
                    else:
                        row = {
                            "period": period,
                            #trend_name: estimate.get("growth", {}),
                            symbol: estimate.get("growth", {}),
                        }
                        data.append(row)

        if len(data) == 0:
            return pd.DataFrame()
        
        df = pd.DataFrame(data).set_index("period").dropna(how='all')
        #df = df.rename(columns={'A': 'Alpha', 'B': 'Beta'})
        return df

    def fetch_all_trends(self, ticker: str) -> dict[str, pd.DataFrame]:
        """모든 추세 데이터 조회"""
        return {
            "earnings_estimate": self.fetch_earnings_estimate(ticker),
            "revenue_estimate": self.fetch_revenue_estimate(ticker),
            "eps_trend": self.fetch_eps_trend(ticker),
            "eps_revisions": self.fetch_eps_revisions(ticker),
        }

    # ==================== Private Methods ====================

    def _fetch_earning_history(self, ticker: str, key: str):
        """
        Earnings Trend 데이터 조회
        
        Args:
            ticker: 종목 심볼
            key: 'earningsHistory'
        """

        result = self.quote_parser.fetch_quote(ticker, modules=[key])
        earnings_history = self._extract_module(result, key)

        if not earnings_history:
            return pd.DataFrame()

        history = earnings_history.get("history", [])

        rows = []
        for item in history:
            row = {
                "quarter": item.get("quarter", {}).get("fmt", None),
            }
            for k, v in item.items():
                if k == "quarter":
                    continue
                
                if isinstance(v, dict) and "raw" in v:
                    row[k] = v.get('raw', None)
            
            rows.append(row)

        if len(history) == 0:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows)
        if "quarter" in df.columns:
            df["quarter"] = pd.to_datetime(df["quarter"], format="%Y-%m-%d")
            df.set_index("quarter", inplace=True)

        return df

    def _fetch_earning_trend(self, ticker: str, key: str, modules: list[str] = ["earningsTrend"]):
        """
        Earnings Trend 데이터 조회
        
        Args:
            ticker: 종목 심볼
            key: 'earningsEstimate', 'revenueEstimate', 'epsTrend', 'epsRevisions'
        """
        result = self.quote_parser.fetch_quote(ticker, modules=modules)
        earnings_trend = self._extract_module(result, "earningsTrend")

        if not earnings_trend:
            return pd.DataFrame()

        trends = earnings_trend.get("trend", [])

        data = []
        for item in trends:
            row = {'period': item.get('period', '')}

            trend_data = item.get(key, {})
            for k, v in trend_data.items():
                if isinstance(v, dict) and "raw" in v:
                    row[k] = v['raw']

            if len(row) > 1:  # period 외에 데이터가 있는 경우만
                data.append(row)
        
        if len(data) == 0:
            return pd.DataFrame()

        return pd.DataFrame(data).set_index('period')
    
    def _extract_module(self, result: dict, module_name: str) -> dict:
        """API 응답에서 특정 모듈 데이터 추출"""
        try:
            return (
                result
                .get("quoteSummary", {})
                .get("result", [{}])[0]
                .get(module_name, {})
            )
        except (IndexError, KeyError, TypeError):
            return {}

    @staticmethod
    def _timestamp_to_date(timestamp: int):
        """Unix timestamp를 date로 변환"""
        if not timestamp:
            return None
        try:
            return datetime.fromtimestamp(timestamp).date()
        except (ValueError, TypeError, OSError):
            return None