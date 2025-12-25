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

logger = logging.getLogger(__name__)

class YahooQuoteParser:
    """
    Yahoo Finance Quote 파싱 클래스

    https://github.com/ranaroussi/yfinance/blob/main/yfinance/scrapers/quote.py
    https://github.com/ranaroussi/yfinance/blob/main/yfinance/scrapers/analysis.py
    """

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

    def fetch(self, ticker: str):
        """
        회사 이름(query)을 받아서 티커로 변환한 뒤,
        Yahoo Finance에서 뉴스를 수집하고, 기사 본문을 크롤링합니다.
        """

        summary_url = f"{_QUOTE_SUMMARY_URL_}/{ticker}"
        params = {
            "modules": ",".join(self.MODULES), 
            "corsDomain": "finance.yahoo.com", 
            "formatted": "false", 
            "symbol": ticker
        }

        if _QUERY2_URL_ in summary_url:
            params["crumb"] = self.fetch_crumb()

        response = self.client._get(summary_url, params=params)
        summary_info = response.json()

        params = {"symbols": ticker, "formatted": "false"}
        params["crumb"] = self.fetch_crumb()

        response = self.client._get(_QUOTE_URL_, params=params)
        quote_info = response.json()

        if quote_info is not None and summary_info is not None:
            summary_info.update(quote_info)
        else:
            summary_info = quote_info

        query_info = {}
        for quote in ['quoteSummary', 'quoteResponse']:
            if quote in summary_info and len(summary_info[quote]['result']) > 0:
                summary_info[quote]['result'][0]["symbol"] = ticker
                query = next(
                    (item for item in summary_info.get(quote, {}).get('result', []) 
                    if item.get('symbol') == ticker), 
                    None
                )
                
                if query:
                    query_info.update(query)

        # Normalize and flatten nested dictionaries while converting maxAge from days (1) to seconds (86400).
        # This handles Yahoo Finance API inconsistency where maxAge is sometimes expressed in days instead of seconds.
        processed_info = {}
        for k, v in query_info.items():
            if isinstance(v, dict):
                for k1, v1 in v.items():
                    if v1 is not None:
                        processed_info[k1] = 86400 if k1 == 'maxAge' and v1 == 1 else v1
            elif v is not None:
                processed_info[k] = v

        query_info = processed_info

        # recursively format but only because of 'companyOfficers'

        def _format(k, v):
            if isinstance(v, dict) and "raw" in v and "fmt" in v:
                v2 = v["fmt"] if k in {"regularMarketTime", "postMarketTime"} else v["raw"]
            elif isinstance(v, list):
                v2 = [_format(None, x) for x in v]
            elif isinstance(v, dict):
                v2 = {k: _format(k, x) for k, x in v.items()}
            elif isinstance(v, str):
                v2 = v.replace("\xa0", " ")
            else:
                v2 = v
            return v2

        return {k: _format(k, v) for k, v in query_info.items()}

    def _datetime_format(self, datetime_str: str):
        # 타임존 매핑
        tz_map = {
            "EST": "-05:00",
            "EDT": "-04:00",
            "PST": "-08:00",
            "PDT": "-07:00",
        }
    
        # 타임존 추출
        tz_abbr = datetime_str.split()[-1]
        tz_offset = tz_map.get(tz_abbr, "-05:00")
        
        # 타임존 제거 후 파싱
        datetime_str_clean = datetime_str.rsplit(" ", 1)[0]  # 'January 29, 2026 at 4 PM'
        
        # 'at' 제거
        datetime_str_clean = datetime_str_clean.replace(" at ", " ")  # 'January 29, 2026 4 PM'
        
        # datetime 파싱
        dt = pd.to_datetime(datetime_str_clean, format="%B %d, %Y %I %p")
        
        # 결과 포맷팅
        return f"{dt.strftime('%Y-%m-%d %H:%M:%S')}{tz_offset}"

    def fetch_recommendation(self, ticker: str, as_dict: bool = False):
        """
        Yahoo Finance Recommendation API 호출
        
        Args:
            ticker: 종목 심볼
        """
        # API 호출
        try:
            response = self.fetch_quote(ticker, modules=["recommendationTrend"])

            if response is None:
                return pd.DataFrame()

            data = response.get("quoteSummary", {}).get("result", [{}])[0].get("recommendationTrend", {}).get("trend", [])

            if as_dict:
                return data.to_dict()

            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Failed to fetch recommendation for {ticker}: {e}")
            return pd.DataFrame()
    
    def fetch_sec_filings(self, ticker: str):
        """
        SEC Filings API 호출
        
        Args:
            ticker: 종목 심볼
        """
        try:
            response = self.fetch_quote(ticker, modules=["secFilings"])

            if response is None:
                return {}

            filings = response.get("quoteSummary", {}).get("result", [{}])[0].get("secFilings", {}).get("filings", [])
            #print(filings)

            for filing in filings:
                if 'exhibits' in filing:
                    filing['exhibits'] = {ex.get("type", ""):ex.get("url", "") for ex in filing.get('exhibits', [{}])}
                filing['date'] = datetime.strptime(filing.get('date', ''), '%Y-%m-%d').date()
            
            return filings

        except Exception as e:
            logger.error(f"Failed to fetch sec filings for {ticker}: {e}")
            return {}

    def fetch_quote(self, ticker: str, modules: list[str]):
        """
        Quote Summary API 호출
        
        Args:
            ticker: 종목 심볼
            modules: 요청할 모듈 목록
        """
        if not modules:
            return {}

        valid_modules = [module for module in modules if module in quote_summary_valid_modules]

        if not valid_modules:
            logger.warning(f"No valid modules: {modules}")
            return {}

        url = f"{_QUOTE_SUMMARY_URL_}/{ticker}"
        params = {
            "modules": ",".join(valid_modules),
            "corsDomain": "finance.yahoo.com",
            "formatted": "false",
            "symbol": ticker
        }

        # 크럼 인증 추가
        if not self._crumb and _QUERY2_URL_ in url:
            self._crumb = self.fetch_crumb()
        
        params["crumb"] = self._crumb

        # API 호출
        try:
            response = self.client._get(url, params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch quote summary for {ticker}: {e}")
            return {}

    def fetch_earning_calendar(self, ticker: str, limit: int = 12, offset: int = 0):
        """
        Yahoo Finance Earning Calendar 획득
        
           Symbol     Company                 Earnings Date  EPS Estimate Reported EPS Surprise (%)
0    AAPL  Apple Inc.  January 29, 2026 at 4 PM EST          2.67            -            -
1    AAPL  Apple Inc.  October 30, 2025 at 4 PM EDT          1.77         1.85        +4.52
2    AAPL  Apple Inc.     July 31, 2025 at 4 PM EDT          1.43         1.57       +10.12
3    AAPL  Apple Inc.       May 1, 2025 at 4 PM EDT          1.62         1.65        +1.69
4    AAPL  Apple Inc.  January 30, 2025 at 4 PM EST          2.34          2.4        +2.52
5    AAPL  Apple Inc.  October 31, 2024 at 4 PM EDT          1.60         1.64        +2.28
6    AAPL  Apple Inc.    August 1, 2024 at 4 PM EDT          1.34          1.4        +4.36
7    AAPL  Apple Inc.       May 2, 2024 at 4 PM EDT          1.50         1.53        +2.05
8    AAPL  Apple Inc.  February 1, 2024 at 4 PM EST          2.10         2.18        +3.66
9    AAPL  Apple Inc.  November 2, 2023 at 4 PM EDT          1.39         1.46        +4.93
10   AAPL  Apple Inc.    August 3, 2023 at 4 PM EDT          1.19         1.26        +5.47
11   AAPL  Apple Inc.       May 4, 2023 at 4 PM EDT          1.43         1.52        +6.28
12   AAPL  Apple Inc.  February 2, 2023 at 4 PM EST          1.95         1.88        -3.78
13   AAPL  Apple Inc.  October 27, 2022 at 4 PM EDT          1.27         1.29        +1.44
14   AAPL  Apple Inc.     July 28, 2022 at 4 PM EDT          1.15          1.2        +3.93
15   AAPL  Apple Inc.    April 28, 2022 at 4 PM EDT          1.43         1.52        +6.48
16   AAPL  Apple Inc.  January 27, 2022 at 4 PM EST          1.89          2.1        +11.2
17   AAPL  Apple Inc.  October 28, 2021 at 4 PM EDT          1.24         1.24        +0.17
18   AAPL  Apple Inc.     July 27, 2021 at 4 PM EDT          1.01          1.3       +28.56
19   AAPL  Apple Inc.    April 28, 2021 at 4 PM EDT          0.98          1.4       +42.16
20   AAPL  Apple Inc.  January 27, 2021 at 4 PM EST          1.42         1.68       +18.67
21   AAPL  Apple Inc.  October 29, 2020 at 4 PM EDT          0.70         0.73         +4.5
22   AAPL  Apple Inc.     July 30, 2020 at 4 PM EDT          0.52         0.65       +24.45
23   AAPL  Apple Inc.    April 30, 2020 at 5 PM EDT          0.56         0.64       +12.93
24   AAPL  Apple Inc.  January 28, 2020 at 4 PM EST          1.13         1.25        +9.97
25    NaN         NaN                           NaN           NaN          NaN          NaN

                   Earnings Date  EPS Estimate Reported EPS Surprise(%)
0   January 29, 2026 at 4 PM EST          2.67            -           -
1   October 30, 2025 at 4 PM EDT          1.77         1.85       +4.52
2      July 31, 2025 at 4 PM EDT          1.43         1.57      +10.12
3        May 1, 2025 at 4 PM EDT          1.62         1.65       +1.69
4   January 30, 2025 at 4 PM EST          2.34          2.4       +2.52
5   October 31, 2024 at 4 PM EDT          1.60         1.64       +2.28
6     August 1, 2024 at 4 PM EDT          1.34          1.4       +4.36
7        May 2, 2024 at 4 PM EDT          1.50         1.53       +2.05
8   February 1, 2024 at 4 PM EST          2.10         2.18       +3.66
9   November 2, 2023 at 4 PM EDT          1.39         1.46       +4.93
10    August 3, 2023 at 4 PM EDT          1.19         1.26       +5.47
11       May 4, 2023 at 4 PM EDT          1.43         1.52       +6.28
12  February 2, 2023 at 4 PM EST          1.95         1.88       -3.78
13  October 27, 2022 at 4 PM EDT          1.27         1.29       +1.44
14     July 28, 2022 at 4 PM EDT          1.15          1.2       +3.93
15    April 28, 2022 at 4 PM EDT          1.43         1.52       +6.48
16  January 27, 2022 at 4 PM EST          1.89          2.1       +11.2
17  October 28, 2021 at 4 PM EDT          1.24         1.24       +0.17
18     July 27, 2021 at 4 PM EDT          1.01          1.3      +28.56
19    April 28, 2021 at 4 PM EDT          0.98          1.4      +42.16
20  January 27, 2021 at 4 PM EST          1.42         1.68      +18.67
21  October 29, 2020 at 4 PM EDT          0.70         0.73        +4.5
22     July 30, 2020 at 4 PM EDT          0.52         0.65      +24.45
23    April 30, 2020 at 5 PM EDT          0.56         0.64      +12.93
24  January 28, 2020 at 4 PM EST          1.13         1.25       +9.97

Earnings Date                                                   
2026-01-29 16:00:00-05:00          2.67            -           -
2025-10-30 16:00:00-04:00          1.77         1.85       +4.52
2025-07-31 16:00:00-04:00          1.43         1.57      +10.12
2025-05-01 16:00:00-04:00          1.62         1.65       +1.69
2025-01-30 16:00:00-05:00          2.34          2.4       +2.52
2024-10-31 16:00:00-04:00          1.60         1.64       +2.28
2024-08-01 16:00:00-04:00          1.34          1.4       +4.36
2024-05-02 16:00:00-04:00          1.50         1.53       +2.05
2024-02-01 16:00:00-05:00          2.10         2.18       +3.66
2023-11-02 16:00:00-04:00          1.39         1.46       +4.93
2023-08-03 16:00:00-04:00          1.19         1.26       +5.47
2023-05-04 16:00:00-04:00          1.43         1.52       +6.28
2023-02-02 16:00:00-05:00          1.95         1.88       -3.78
2022-10-27 16:00:00-04:00          1.27         1.29       +1.44
2022-07-28 16:00:00-04:00          1.15          1.2       +3.93
2022-04-28 16:00:00-04:00          1.43         1.52       +6.48
2022-01-27 16:00:00-05:00          1.89          2.1       +11.2
2021-10-28 16:00:00-04:00          1.24         1.24       +0.17
2021-07-27 16:00:00-04:00          1.01          1.3      +28.56
2021-04-28 16:00:00-04:00          0.98          1.4      +42.16
2021-01-27 16:00:00-05:00          1.42         1.68      +18.67
2020-10-29 16:00:00-04:00          0.70         0.73        +4.5
2020-07-30 16:00:00-04:00          0.52         0.65      +24.45
2020-04-30 17:00:00-04:00          0.56         0.64      +12.93
2020-01-28 16:00:00-05:00          1.13         1.25       +9.97
        """

        # limit validation
        if limit > 0 and limit <= 25:
            size = 25
        elif limit > 25 and limit <= 50:
            size = 50
        elif limit > 50 and limit <= 100:
            size = 100
        else:
            raise ValueError("limit must be between 1 and 100")
        
        url = f"{_ROOT_URL_}/calendar/earnings"
        params = {
            "symbol": ticker,
            "offset": offset,
            "size": size,
        }
        response = self.client._get(url, params=params)

        # Parse HTML response
        soup = BeautifulSoup(response.content, "html.parser")

        table = soup.find("table")
        if not table:
            return pd.DataFrame()
        
        # 테이블을 DataFrame으로 변환
        table_html = str(table)
        df = pd.read_html(StringIO(table_html))[0]

        # 불필요한 컬럼 제거
        df = df.drop(["Symbol", "Company"], axis=1)

        # 컬럼명 변경
        df.rename(columns={'Surprise (%)': 'Surprise(%)'}, inplace=True)

        df = df.dropna(subset=["Earnings Date"])

        # datetime 포맷팅
        df = df.copy()
        df["Earnings Date"] = df["Earnings Date"].apply(self._datetime_format)
        df = df.set_index("Earnings Date")

        return df    

    def fetch_crumb(self):
        """Yahoo Finance 크럼(인증 토큰) 획득"""
        if self._crumb:
            return self._crumb

        self.client._get(_ROOT_URL_)

        response = self.client._get(_CRUMB_URL_)
        self._crumb = response.content.decode("utf-8").strip()
        return self._crumb
        