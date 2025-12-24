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
import random
import time
import yfinance as yf

from bs4 import BeautifulSoup, Tag
from datetime import datetime, timedelta
from io import StringIO
from typing import Any, Optional

from ..client import YahooClient
from ..utils import (
    _ROOT_URL_,
    _QUERY1_URL_,
    _QUERY2_URL_,
    _QUOTE_SUMMARY_URL_,
    _QUOTE_URL_,
    _CRUMB_URL_,
    quote_summary_valid_modules
)
from .quote import YahooQuoteParser

logger = logging.getLogger(__name__)

class YahooSummaryParser:
    """
    Yahoo Finance Summary 파싱 클래스

    https://github.com/ranaroussi/yfinance/blob/main/yfinance/scrapers/quote.py
    https://github.com/ranaroussi/yfinance/blob/main/yfinance/scrapers/analysis.py
    """

    MODULES = [
        "calendarEvents",
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

    def fetch_summary(self, ticker: str):
        """
        기업 정보 조회
        회사 이름(query)을 받아서 티커로 변환한 뒤,
        Yahoo Finance에서 뉴스를 수집하고, 기사 본문을 크롤링합니다.

        Returns:
            dict[str, str]: 
            {
            'Previous Close': '481.20', 
            'Open': '489.88', 
            'Bid': '469.66 x 200', 
            'Ask': '470.10 x 100', 
            "Day's Range": '485.33 - 498.82', 
            '52 Week Range': '214.25 - 498.82', 
            'Volume': '86,555,000', 
            'Avg. Volume': '85,835,588', 
            'Market Cap (intraday)': '1.625T', 
            'Beta (5Y Monthly)': '1.88', 
            'PE Ratio (TTM)': '332.47', 
            'EPS (TTM)': '1.47', 
            'Earnings Date (est.)': '2026-01-29', 
            'Forward Dividend & Yield': 'N/A', 
            'Ex-Dividend Date': 'N/A', 
            '1y Target Est': '397.43'
            }
        """

        summary_url = f"{_QUOTE_SUMMARY_URL_}/{ticker}"
        params = {
            "modules": ",".join(self.MODULES), 
            "corsDomain": "finance.yahoo.com", 
            "formatted": "false", 
            "symbol": ticker
        }

        if _QUERY2_URL_ in summary_url:
            params["crumb"] = self.quote_parser.fetch_crumb()

        response = self.client._get(summary_url, params=params)
        summary_info = response.json()

        return self._format_summary_data(summary_info)

    def _format_summary_data(self, data: dict[str, Any]) -> dict[str, str]:
        """
        Yahoo Finance quoteSummary JSON에서 요약 데이터를 추출합니다.
        
        Args:
            data: Yahoo Finance API 응답 데이터
            
        Returns:
            포맷팅된 요약 정보 딕셔너리
        """
        result = data['quoteSummary']['result'][0]
        summary = result.get('summaryDetail', {})
        key_stats = result.get('defaultKeyStatistics', {})
        financial = result.get('financialData', {})

        # calendarEvents
        calendar_events = result.get('calendarEvents', {})
        earnings = calendar_events.get('earnings', {})

        # earningsDate는 리스트로 제공됨 (시작일, 종료일)
        earnings_dates = earnings.get('earningsDate', [])
        
        def format_number(value: float | int, decimals: int = 2) -> str:
            """숫자를 천 단위 구분자로 포맷팅"""
            if isinstance(value, float):
                return f"{value:,.{decimals}f}"
            return f"{value:,}"
        
        def format_market_cap(value: int) -> str:
            """시가총액을 T/B 단위로 포맷팅"""
            if value >= 1e12:
                return f"{value / 1e12:.3f}T"
            elif value >= 1e9:
                return f"{value / 1e9:.3f}B"
            elif value >= 1e6:
                return f"{value / 1e6:.3f}M"
            return format_number(value)
        
        def format_epoch_date(epoch: int) -> str:
            """Epoch 타임스탬프를 날짜 문자열로 변환"""
            from datetime import datetime
            dt = datetime.fromtimestamp(epoch)
            #return dt.strftime("%b %d, %Y")
            return dt.strftime("%Y-%m-%d")

        earnings_date = format_epoch_date(earnings_dates[0]) if earnings_dates else "N/A"
        
        dividend_rate = summary.get('dividendRate', 0)
        dividend_yield = summary.get('dividendYield', 0)
        dividend_yield = f"{format_number(dividend_rate)} ({format_number(dividend_yield * 100)}%)" if dividend_rate > 0 else "N/A"
        ex_dividend_date = summary.get('exDividendDate')
        ex_dividend_date = format_epoch_date(ex_dividend_date) if ex_dividend_date else "N/A"
        
        return {
            "Previous Close": format_number(summary['previousClose']),
            "Open": format_number(summary['open']),
            "Bid": f"{format_number(summary['bid'])} x {format_number(summary['bidSize'], 0)}",
            "Ask": f"{format_number(summary['ask'])} x {format_number(summary['askSize'], 0)}",
            "Day's Range": f"{format_number(summary['dayLow'])} - {format_number(summary['dayHigh'])}",
            "52 Week Range": f"{format_number(summary['fiftyTwoWeekLow'])} - {format_number(summary['fiftyTwoWeekHigh'])}",
            "Volume": format_number(summary['volume'], 0),
            "Avg. Volume": format_number(summary['averageVolume'], 0),
            "Market Cap (intraday)": format_market_cap(summary['marketCap']),
            "Beta (5Y Monthly)": format_number(key_stats['beta']),
            "PE Ratio (TTM)": format_number(summary['trailingPE']),
            "EPS (TTM)": format_number(key_stats['trailingEps']),
            "Earnings Date (est.)": earnings_date,
            "Forward Dividend & Yield": dividend_yield,
            "Ex-Dividend Date": ex_dividend_date,
            "1y Target Est": format_number(financial['targetMeanPrice']),
        }
