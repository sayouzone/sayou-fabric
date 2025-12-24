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
 
import ast
import logging
import pandas as pd
import random
import re
import time

from bs4 import BeautifulSoup, Tag
from io import StringIO
from typing import Dict, Any, List, Tuple, Optional

from ..client import NaverClient
from ..utils import (
    NEWS_URLS,
    FINANCE_URL,
    FINANCE_API_URL,
    MOBILE_URL,
    decode_euc_kr
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NaverMarketParser:

    # 종합
    mobile_price_url = "https://m.stock.naver.com/api/stock/{code}/total"
    # 뉴스·공시
    mobile_price_url = "https://m.stock.naver.com/api/stock/{code}/news"
    # 시세
    mobile_price_url = "https://m.stock.naver.com/api/stock/{code}/price"
    # 종목 정보
    mobile_price_url = "https://m.stock.naver.com/api/stock/{code}/basic"
    mobile_price_url = "https://m.stock.naver.com/api/stock/{code}/integration"
    "https://api.finance.naver.com/siseJson.naver?symbol=005930&requestType=1&startTime=20250901&endTime=20251231&timeframe=day&order=desc&output=json"
    "https://finance.naver.com/item/sise_time.naver?code=005930&thistime=20251218134521"
    "https://finance.naver.com/item/sise_day.naver?code=005930"
    "https://finance.naver.com/item/main.naver?code=005930"
    "https://finance.naver.com/item/sise.naver?code=005930"
    "https://finance.naver.com/item/item_right_ajax.naver?type=recent&code=005930&page=1"

    sise_columns = {
        '날짜': 'date',
        '시가': 'open',
        '고가': 'high',
        '저가': 'low',
        '종가': 'close',
        '거래량': 'volume'
    }

    def __init__(self, client: NaverClient):
        self.client = client

    def fetch(
        self,
        code: str | None = None, 
        start_date: str | None = None, 
        end_date: str | None = None, 
        max_page: int = 100
    ) -> pd.DataFrame:
        """
        기업 코드로 시작일과 종료일 사이 일별 시세를 조회한다.
        한 페이지의 크기는 10으로 고정되어 있음 (Gemini 답변)

        Args:
            code (str): 기업 코드, 예: 005930 (삼성전자)
            start_date (str): 시작일, 예: 2025-09-01
            end_date (str): 종료일, 예: 2025-12-31
            max_page (int): 최대 페이지 수

        Returns:
            일별 시세 DataFrame
        """
        
        if not code:
            return pd.DataFrame()

        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        
        """
        # 속도가 느림, 처리 프로세스도 복잡함
        market_prices = self._fetch_historical_data(code, start_date=start_date, max_page=max_page)
        # Filter by date range
        market_prices = market_prices[
            (market_prices['date'] >= pd.to_datetime(start_date)) &
            (market_prices['date'] <= pd.to_datetime(end_date))
        ]
        print(market_prices, type(market_prices))
        """
        
        market_prices = self._fetch_sise_data(code, start_date=start_date, end_date=end_date)
        #print(market_prices, type(market_prices))

        if market_prices.empty:
            print("type:", "error", ",", "message:", "Failed to crawl market data.")
            return pd.DataFrame()

        return market_prices
    
    def _fetch_sise_data(
        self,
        code: str,
        start_date: str | None = None,
        end_date: str | None = None
    ) -> pd.DataFrame:
        """
        기업 코드로 시작일부터 종료일까지 일별 시세를 조회한다.
        한글 키를 영어로 변환. 예: '날짜': 'date'

        Args:
            code (str): 기업 코드, 예: 005930 (삼성전자) 
            start_date (str): 시작일, 예: 20250901
            end_date (str): 종료일, 예: 20251231

        Returns:
            일별 시세 DataFrame
        """

        params = {
            "symbol": code,
            "requestType": 1,
            "startTime": start_date.replace("-",""),
            "endTime": end_date.replace("-",""),
            "timeframe": "day",
            "order": "asc",
            "output": "json"
        }
        
        url = f"{FINANCE_API_URL}/siseJson.naver"

        #print(url, params)
        response = self.client._get(url, params=params)
        #print(f"Header: {response.headers}, Content: {response.content}")
        
        # 응답이 JSON이 아닌 JavaScript 배열 형태로 옴
        # 예: [["날짜","시가","고가","저가","종가","거래량"], ["20250901",55000,...], ...]
        text = response.text.strip()
        
        # eval 대신 안전하게 파싱
        # 작은따옴표를 큰따옴표로 변환하고 파싱
        text = text.replace("'", '"')
        data = ast.literal_eval(text)
        
        # 첫 번째 행은 헤더
        headers = [col.strip() for col in data[0]]
        rows = data[1:]
        
        df = pd.DataFrame(rows, columns=headers)
        
        # 날짜 컬럼 변환
        if "날짜" in df.columns:
            df["날짜"] = pd.to_datetime(df["날짜"], format="%Y%m%d")
        
        # 숫자 컬럼 변환
        numeric_cols = ["시가", "고가", "저가", "종가", "거래량"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        columns = self.sise_columns
        columns['외국인소진율'] = 'foreign_investment_rate'
        df.rename(columns=columns, inplace=True)
        
        return df
        
    def _fetch_historical_data(
        self,
        code: str,
        start_date: str | None = None,
        max_page: int = 99999
    ) -> pd.DataFrame:
        """
        기업 코드로 시작일부터 현재까지 일별 시세를 조회한다.
        한글 키를 영어로 변환. 예: '날짜': 'date'

        Args:
            code (str): 기업 코드, 예: 005930 (삼성전자) 
            start_date (str): 시작일, 예: 2025-09-01
            max_page (int): 최대 페이지 수

        Returns:
            일별 시세 DataFrame
        """
        last_page = max_page
        
        full_df = []
        page = 1
        while True:
            try:
                params = {
                    "code": code,
                    "page": page
                }

                url = f"{FINANCE_URL}/item/sise_day.nhn"
                #print(f"Parsing URL: {url}, params: {params}")

                response = self.client._get(url, params=params)

                # Response Header에서 Content-Type, Charset 추출
                content_type = response.headers.get("content-type", "")
                # 정규식 검색: charset= 뒤에 오는 문자열(알파벳, 숫자, 하이픈)을 찾음
                match = re.search(r'charset=([\w-]+)', content_type, re.IGNORECASE)
                charset = match.group(1).lower() if match else None
                #print(response.headers, charset)

                content = decode_euc_kr(response)
                #print(content)
        
                if last_page == max_page:
                    _last_page = self._find_last_page(content)
                    last_page = min(max_page, _last_page)
                    #print(_last_page, last_page)
        
                dfs = pd.read_html(StringIO(content))
                df = dfs[0]
                df.dropna(how='all', inplace=True)
                #print(df)
                
                if df.empty:
                    break
                
                full_df.append(df)
        
                if start_date:
                    # 현재 페이지에서 가장 과거 날짜 확인
                    # 네이버 금융 날짜 포맷은 'YYYY.MM.DD' 이므로 문자열 비교 가능
                    min_date = df['날짜'].min().replace(".", "-")
                    #print(f"Min Date: {min_date}, {type(min_date)}")
                    
                    # 현재 페이지의 가장 옛날 날짜가 설정한 시작일보다 작거나 같으면
                    # 더 과거로 갈 필요가 없으므로 루프 종료
                    if min_date <= start_date:
                        #print(f"Reached start_date limit: {min_date} <= {start_date}")
                        break
                
                #print(page, last_page)
                if page >= last_page:
                    break
        
                page += 1
                time.sleep(random.uniform(0.1, 0.3))
            except Exception as exc:
                print(f"Error scraping page {page}: {exc}")
                continue
                
        crawled_df = pd.concat(full_df, ignore_index=True)
        columns = self.sise_columns
        crawled_df.rename(columns=columns, inplace=True)
        
        if '전일비' in crawled_df.columns:
            crawled_df.drop(columns=['전일비'], inplace=True)
        
        numeric_cols = ['close', 'open', 'high', 'low', 'volume']
        for col in numeric_cols:
            if col in crawled_df.columns:
                crawled_df[col] = pd.to_numeric(
                    crawled_df[col].astype(str).str.replace(',', '', regex=False),
                    errors='coerce'
                ).fillna(0)
                if col == 'volume':
                    crawled_df[col] = crawled_df[col].astype('int64')
        
        crawled_df['date'] = pd.to_datetime(crawled_df['date'], errors='coerce')
        crawled_df.dropna(subset=['date'], inplace=True)
        return crawled_df

    def fetch_main_prices(
        self,
        code: str | None = None, 
    ):
        """
        현재 종목의 주요 시세를 스크래핑하여 숫자로 반환합니다.

        Args:
            code (str): 기업 코드, 예: 005930 (삼성전자)

        Returns:
            시가 총액 정수값
        """
        

        params = {
            "code": code
        }
        url = f'{FINANCE_URL}/item/sise.naver'
        response = self.client._get(url, params=params)
        content = decode_euc_kr(response)

        soup = BeautifulSoup(content, 'html.parser')

        # caption이 "주요시세"인 테이블 찾기
        table = soup.find("table", summary=lambda x: x and "주요시세" in x)
        if not table:
            table = soup.find("caption", string="주요시세")
            if table:
                table = table.find_parent("table")
        
        if not table:
            print("주요시세 테이블을 찾을 수 없습니다.")
            return None
        
        #print(table, type(table))
        df_main_prices = self._extract_stock_data(table)
        #print(df_main_prices)

        return df_main_prices

    def fetch_company_metadata(
        self,
        code: str
    ) -> Dict[str, Any]:
        """
        기업의 메타데이터를 조회합니다.
        기업명, 주식 거래소, 환율, 시가 총액 등

        Args:
            code (str): 기업 코드, 예: 005930 (삼성전자)

        Returns:
            기업 메타데이터 Dictionary
        """
        metadata: Dict[str, Any] = {}
        latest_price: float | None = None

        url = f"{MOBILE_URL}/{code}/basic"
        print(f"Parsing URL: {url}")
        response = self.client._get(url)

        basic_json = response.json()

        # 주식 이름
        metadata["company_name"] = basic_json.get("stockName")

        # 주식 거래 형태
        exchange_info = basic_json.get("stockExchangeType") or {}
        metadata["exchange"] = (
            exchange_info.get("name")
            or basic_json.get("stockExchangeName")
        )
        # 환율
        metadata["currency"] = (
            self._infer_currency(exchange_info.get("nationCode"))
            or "KRW"
        )

        closing_price = basic_json.get("closePrice")
        if closing_price is not None:
            try:
                latest_price = float(str(closing_price).replace(',', ''))
            except ValueError:
                latest_price = None

        url = f"{FINANCE_API_URL}/service/itemSummary.naver"
        referer = f'{FINANCE_URL}/item/main.nhn?code={code}'
        print(f"Parsing URL: {url}")
        params = {
            "itemcode": code
        }
        
        response = self.client._get(url, params=params, referer=referer)
        
        summary_json = response.json()
        print(summary_json)
        market_sum = summary_json.get("marketSum")
        if isinstance(market_sum, (int, float)):
            market_cap = float(market_sum) * 1_000_000  # marketSum is in million KRW
            metadata["market_cap"] = market_cap
            if latest_price and latest_price > 0:
                metadata["shares_outstanding"] = int(round(market_cap / latest_price))
        else:
            metadata.setdefault("_warnings", []).append("marketSum missing")

        return metadata

    def _find_last_page(
        self,
        html_text: str
    ) -> int:
        """
        기업 일별 시세에 대한 최대 페이지를 확인

        Args:
            html_text (str): HTML 텍스트에서 마지막 페이지 번호 확인

        Returns:
            마지막 페이지 번호
        """
        soup = BeautifulSoup(html_text, 'html.parser')
        match = None
        pg_rr_tag = soup.select_one('.pgRR a')
        
        if pg_rr_tag:
            href_value = pg_rr_tag.get('href')
            if isinstance(href_value, str):
                match = re.search(r'page=(\d+)', href_value)
    
        if match:
            last_page = int(match.group(1))
        else:
            last_page = 1
    
        return last_page

    def _extract_stock_data(self, table: Tag) -> pd.DataFrame | None:
        """주요시세 테이블에서 데이터를 추출하여 DataFrame으로 반환"""
        
        # 데이터 추출
        data = {}
        rows = table.find_all("tr")
        
        for row in rows:
            headers = row.find_all("th")
            values = row.find_all("td")
            
            # th-td 쌍으로 데이터 추출 (한 행에 2쌍씩 있는 구조)
            if len(headers) >= 1 and len(values) >= 1:
                for i, th in enumerate(headers):
                    key = th.get_text(strip=True)
                    if i < len(values):
                        # td 내부의 텍스트만 추출 (단위 포함)
                        value = values[i].get_text(strip=True)
                        # "하락", "상승" 등의 blind 텍스트 제거
                        value = value.replace("하락", "").replace("상승", "").strip()
                        data[key] = value
        
        # DataFrame 생성 (단일 행)
        df = pd.DataFrame([data])
        return df

    def _infer_currency(self, nation_code: str | None) -> str | None:
        if not nation_code:
            return None
        nation_code = nation_code.upper()
        if nation_code in {'KOR', 'KR'}:
            return 'KRW'
        if nation_code in {'USA', 'US'}:
            return 'USD'
        if nation_code in {'JPN', 'JP'}:
            return 'JPY'
        if nation_code in {'CHN', 'CN'}:
            return 'CNY'
        return None