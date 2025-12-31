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
from ..models import (
    Currency,
    StockPrice,
    MainPrices,
    CompanyMetadata,
    PriceHistory,
    SiseRequest,
)
from ..utils import (
    NEWS_URLS,
    FINANCE_URL,
    FINANCE_API_URL,
    MOBILE_URL,
    SISE_COLUMNS,
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

    DEFAULT_HISTORY_DAYS = 180
    DEFAULT_DELAY_RANGE = (0.1, 0.3)

    # API URL 템플릿
    class URLs:
        SISE_JSON = f"{FINANCE_API_URL}/siseJson.naver"
        SISE_DAY = f"{FINANCE_URL}/item/sise_day.nhn"
        SISE_MAIN = f"{FINANCE_URL}/item/sise.naver"
        ITEM_SUMMARY = f"{FINANCE_API_URL}/service/itemSummary.naver"
        MOBILE_BASIC = f"{MOBILE_URL}/{{code}}/basic"

    def __init__(self, client: NaverClient):
        self.client = client

    def fetch(
        self,
        code: Optional[str] = None,
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None, 
        max_page: int = 100
    ) -> pd.DataFrame:
        """
        기업 코드로 시작일과 종료일 사이 일별 시세를 조회한다.
        한 페이지의 크기는 10으로 고정되어 있음 (Gemini 답변)

        Args:
            code: 기업 코드, (예: 005930, 삼성전자)
            start_date: 시작일 (YYYY-MM-DD), (예: 2025-09-01)
            end_date: 종료일 (YYYY-MM-DD), (예: 2025-12-31)
            max_page: 최대 페이지 수

        Returns:
            일별 시세 DataFrame
        """
        
        if not code:
            return pd.DataFrame()

        end_date = end_date or datetime.now().strftime('%Y-%m-%d')
        start_date = start_date or (datetime.now() - timedelta(days=self.DEFAULT_HISTORY_DAYS)).strftime('%Y-%m-%d')

        request = SiseRequest(
            code=code,
            start_date=start_date,
            end_date=end_date,
            max_page=max_page
        )
        
        market_prices = self._fetch_sise_data(request)
        #print(market_prices, type(market_prices))

        if market_prices.empty:
            print("type:", "error", ",", "message:", "Failed to crawl market data.")
            return pd.DataFrame()

        return market_prices

    def fetch_main_prices(
        self,
        code: Optional[str] = None 
    ) -> Optional[MainPrices]:
        """
        현재 종목의 주요 시세를 스크래핑하여 숫자로 반환합니다.

        Args:
            code: 기업 코드, (예: 005930, 삼성전자)

        Returns:
            MainPrices 데이터 모델 또는 None
        """
        if not code:
            return None

        params = { "code": code }
        response = self.client._get(self.URLs.SISE_MAIN, params=params)
        content = decode_euc_kr(response)

        soup = BeautifulSoup(content, 'html.parser')
        table = self._find_main_prices_table(soup)
        
        if not table:
            print("주요시세 테이블을 찾을 수 없습니다.")
            return None
        
        raw_data = self._extract_table_data(table)
        return MainPrices.from_raw_data(raw_data)

    def fetch_company_metadata(self, code: str) -> CompanyMetadata:
        """
        기업의 메타데이터를 조회합니다.
        기업명, 주식 거래소, 환율, 시가 총액 등

        Args:
            code (str): 기업 코드, 예: 005930 (삼성전자)

        Returns:
            CompanyMetadata 데이터 모델
        """
        metadata = CompanyMetadata(code=code)

        # 기본 정보 조회
        self._fetch_basic_info(metadata)

        # 시가총액 정보 조회
        self._fetch_market_cap_info(metadata)

        return metadata
    
    def _fetch_sise_data(self, request: SiseRequest) -> pd.DataFrame:
        """
        기업 코드로 시작일부터 종료일까지 일별 시세를 조회한다.
        한글 키를 영어로 변환. 예: '날짜': 'date'

        Args:
            request: SiseRequest

        Returns:
            일별 시세 DataFrame
        """
        
        params = request.to_api_params()
        response = self.client._get(self.URLs.SISE_JSON, params=params)
        
        # 응답이 JSON이 아닌 JavaScript 배열 형태로 옴
        # 예: [["날짜","시가","고가","저가","종가","거래량"], ["20250901",55000,...], ...]
        # eval 대신 안전하게 파싱
        # 작은따옴표를 큰따옴표로 변환하고 파싱
        text = response.text.strip().replace("'", '"')

        try:
            data = ast.literal_eval(text)
        except (ValueError, SyntaxError) as e:
            print(f"Error parsing response: {e}")
            return pd.DataFrame()
        
        # 첫 번째 행은 헤더
        headers = [col.strip() for col in data[0]]
        rows = data[1:]
        
        df = pd.DataFrame(rows, columns=headers)

        # 데이터 변환
        df = self._convert_sise_data(df)

        # 컬럼명 영문화
        column_mapping = {**SISE_COLUMNS, "외국인소진율": "foreign_investment_rate"}
        df.rename(columns=column_mapping, inplace=True)
        
        return df
        
    def _fetch_historical_data(self, request: SiseRequest) -> pd.DataFrame:
        """
        기업 코드로 시작일부터 현재까지 일별 시세를 조회한다.
        한글 키를 영어로 변환. 예: '날짜': 'date'

        Args:
            request: SiseRequest

        Returns:
            일별 시세 DataFrame
        """
        all_data: List[pd.DataFrame] = []
        page = 1
        last_page = request.max_page
        
        while page <= last_page:
            try:
                params = { "code": request.code, "page": page }

                logger.info(f"Parsing URL: {self.URLs.SISE_DAY}, params: {params}")
                response = self.client._get(self.URLs.SISE_DAY, params=params)
                content = decode_euc_kr(response)

                # 최대 페이지 수 업데이트
                if page == 1:
                    _last_page = self._find_last_page(content)
                    last_page = min(request.max_page, _last_page)

                dfs = pd.read_html(StringIO(content))
                df = dfs[0].dropna(how='all')

                if df.empty:
                    break

                all_data.append(df)

                if request.start_date and self._check_start_date(df, request.start_date):
                    break
        
                page += 1
                time.sleep(random.uniform(*self.DEFAULT_DELAY_RANGE))
            except Exception as exc:
                logger.error(f"Error scraping page {page}: {exc}")
                continue

        if not all_data:
            return pd.DataFrame()

        return self._process_historical_data(pd.concat(all_data, ignore_index=True))

    def _fetch_basic_info(self, metadata: CompanyMetadata) -> None:
        url = self.URLs.MOBILE_BASIC.format(code=metadata.code)
        logger.info(f"Parsing URL: {url}")

        response = self.client._get(url)
        data = response.json()

        # 주식 이름
        metadata.company_name = data.get("stockName")

        # 주식 거래 형태
        exchange_info = data.get("stockExchangeType") or {}
        metadata.exchange = exchange_info.get("name") or data.get("stockExchangeName")

        nation_code = exchange_info.get("nationCode")
        currency = Currency.from_nation_code(nation_code)
        metadata.currency = currency.value if currency else "KRW"

        closing_price = data.get("closePrice")
        if closing_price is not None:
            try:
                metadata.latest_price = float(str(closing_price).replace(",", ""))
            except ValueError:
                pass

    def _fetch_market_cap_info(self, metadata: CompanyMetadata) -> None:
        """시가총액 정보 API 호출"""
        referer = f'{FINANCE_URL}/item/main.nhn?code={metadata.code}'
        params = { "itemcode": metadata.code }

        logger.info(f"Parsing URL: {self.URLs.ITEM_SUMMARY}")        
        response = self.client._get(self.URLs.ITEM_SUMMARY, params=params, referer=referer)
        
        data = response.json()
        logger.debug(f"Summary response: {data}")

        market_sum = data.get("marketSum")
        if isinstance(market_sum, (int, float)):
            metadata.market_cap = float(market_sum) * 1_000_000  # marketSum is in million KRW
            metadata.calculate_shares_outstanding()
        else:
            metadata.add_warning("marketSum missing")

    def _find_main_prices_table(self, soup: BeautifulSoup) -> Optional[Tag]:
        """주요시세 테이블을 찾습니다."""
        # caption이 "주요시세"인 테이블 찾기
        # summary 속성으로 찾기
        table = soup.find("table", summary=lambda x: x and "주요시세" in x)
        if table:
            return table
        
        # caption으로 찾기
        caption = soup.find("caption", string="주요시세")
        if caption:
            table = caption.find_parent("table")
        
        return None

    def _extract_table_data(self, table: Tag) -> pd.DataFrame | None:
        """주요시세 테이블에서 데이터를 추출하여 DataFrame으로 반환"""
        
        # 데이터 추출
        data = {}
        
        for row in table.find_all("tr"):
            headers = row.find_all("th")
            values = row.find_all("td")
            
            # th-td 쌍으로 데이터 추출 (한 행에 2쌍씩 있는 구조)
            for i, th in enumerate(headers):
                key = th.get_text(strip=True)
                if i < len(values):
                    # td 내부의 텍스트만 추출 (단위 포함)
                    value = values[i].get_text(strip=True)
                    # "하락", "상승" 등의 blind 텍스트 제거
                    value = value.replace("하락", "").replace("상승", "").strip()
                    data[key] = value
        
        return data

    def _find_last_page(self, html_text: str) -> int:
        """
        기업 일별 시세에 대한 최대 페이지를 확인

        Args:
            html_text (str): HTML 텍스트에서 마지막 페이지 번호 확인

        Returns:
            마지막 페이지 번호
        """
        soup = BeautifulSoup(html_text, 'html.parser')
        pg_rr_tag = soup.select_one('.pgRR a')
        
        if pg_rr_tag:
            href_value = pg_rr_tag.get('href')
            if isinstance(href_value, str):
                match = re.search(r'page=(\d+)', href_value)
    
                if match:
                    return int(match.group(1))
    
        return 1

    def _check_start_date(self, df: pd.DataFrame, start_date: str) -> bool:
        # 현재 페이지에서 가장 과거 날짜 확인
        # 네이버 금융 날짜 포맷은 'YYYY.MM.DD' 이므로 문자열 비교 가능
        if "날짜" not in df.columns:
            return False
        
        min_date = df['날짜'].min().replace(".", "-")
        #print(f"Min Date: {min_date}, {type(min_date)}")
        return min_date <= start_date

    def _convert_sise_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """일별 시세 DataFrame을 변환한다."""
        # 날짜 컬럼 변환
        if "날짜" in df.columns:
            df["날짜"] = pd.to_datetime(df["날짜"], format="%Y%m%d")
        
        # 숫자 컬럼 변환
        numeric_cols = ["시가", "고가", "저가", "종가", "거래량"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df

    def _process_historical_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """크롤링된 과거 데이터 후처리"""
        df.rename(columns=SISE_COLUMNS, inplace=True)
        
        if '전일비' in df.columns:
            df.drop(columns=['전일비'], inplace=True)
        
        # 숫자 컬럼 변환
        numeric_cols = ['close', 'open', 'high', 'low', 'volume']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(',', '', regex=False),
                    errors='coerce'
                ).fillna(0)

                if col == 'volume':
                    df[col] = df[col].astype('int64')
        
        # 날짜 컬럼 변환
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df.dropna(subset=['date'], inplace=True)
        
        return df