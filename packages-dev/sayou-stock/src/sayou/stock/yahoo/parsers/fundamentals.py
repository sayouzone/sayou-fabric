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

from ..client import YahooClient
from ..utils import (
    _QUERY1_URL_,
    _QUERY2_URL_,
    _QUOTE_SUMMARY_URL_,
    _FUNDAMENTALS_TIMESERIES_URL_,
    fundamentals_keys
)

logger = logging.getLogger(__name__)

class YahooFundamentalsParser:
    """
    MCP 도구 기반 재무제표 수집 클래스 (캐싱 기능 포함)

    기존 복잡한 분석 로직을 제거하고, 재무제표 3종만 수집하는 단순하고 명확한 구조로 리팩토링.
    GCS 캐싱 기능은 유지하여 API 호출 비용을 최소화.

    https://github.com/ranaroussi/yfinance/blob/main/yfinance/scrapers/fundamentals.py
    """

    TIMESCALE_MAPPING = {"yearly": "annual", "quarterly": "quarterly", "trailing": "trailing"}

    def __init__(self, client: YahooClient):
        self.client = client
        self._crumb: Optional[str] = None

    def fetch_financials(
        self, 
        ticker: str | None = None, 
        name: str | None = None, 
        timescale: str | None = None) -> pd.DataFrame:
        """
        Args:
            ticker: 종목 심볼 (예: 'TSLA')
            name: 재무제표 종류 ('income', 'balance-sheet', 'cash-flow')
            timescale: 기간 ('yearly', 'quarterly', 'trailing')
        """
        # 손익계산서, 재무상태표, 현금흐름표
        allowed_names = ["income", "balance-sheet", "cash-flow"]
        allowed_timescales = ["yearly", "quarterly", "trailing"]

        if name not in allowed_names:
            raise ValueError(f"Invalid name: {name}. Must be one of {allowed_names}")
        if timescale not in allowed_timescales:
            raise ValueError(f"Invalid timescale: {timescale}. Must be one of {allowed_timescales}")

        timescale = self.TIMESCALE_MAPPING[timescale]

        name = "financials" if name == "income" else name
        keys = fundamentals_keys[name]

        # Yahoo returns maximum 4 years or 5 quarters, regardless of start_dt:
        start_dt = datetime(2016, 12, 31)
        end_ts = int(pd.Timestamp.utcnow().ceil("D").timestamp())

        url = f"{_FUNDAMENTALS_TIMESERIES_URL_}/{ticker}"
        params = {
            "symbol": ticker,
            "type": ",".join([timescale + k for k in keys]),
            "period1": int(start_dt.timestamp()),
            "period2": end_ts
        }

        response = self.client._get(url, params=params)
        df = self._timeseries_to_dataframe(response.json())

        return df

    def _timeseries_to_dataframe(self, data: dict) -> pd.DataFrame:
        """
        Yahoo Finance timeseries API 응답을 DataFrame으로 변환
        
        Args:
            data: Yahoo Finance timeseries API 응답 dict
        
        Returns:
            재무제표 DataFrame (행: 항목, 열: 날짜)
        """
        results = data.get("timeseries", {}).get("result", [])
        
        if not results:
            return pd.DataFrame()
        
        records = []
        
        for item in results:
            meta = item.get("meta", {})
            item_type = meta.get("type", [""])[0]  # 예: 'annualTotalRevenue'
            
            # 데이터가 있는 키 찾기 (meta, timestamp 제외)
            for key, values in item.items():
                if key in ("meta", "timestamp") or not isinstance(values, list):
                    continue
                
                # 각 기간별 데이터 추출
                for val in values:
                    if isinstance(val, dict) and "reportedValue" in val:
                        records.append({
                            "item": key,
                            "date": val.get("asOfDate"),
                            "value": val.get("reportedValue", {}).get("raw"),
                            "formatted": val.get("reportedValue", {}).get("fmt"),
                            "currencyCode": val.get("currencyCode"),
                            "periodType": val.get("periodType"),
                        })
        
        if not records:
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        
        # 피벗: 행=항목, 열=날짜
        df_pivot = df.pivot_table(
            index="item",
            columns="date",
            values="value",
            aggfunc="first"
        )
        
        # 컬럼 정렬 (날짜순)
        df_pivot = df_pivot.reindex(sorted(df_pivot.columns, reverse=True), axis=1)
        
        # 인덱스를 컬럼으로 변환
        df_pivot = df_pivot.reset_index()
        
        return df_pivot

    def fundamentals(
        self,
        stock: str | None = None,
        query: str | None = None,
        overwrite: bool = False,
        attribute_name_str: str | None = None
    ) -> dict[str, object]:
        """
        Yahoo Finance에서 재무제표 3종을 수집합니다.

        Args:
            stock: 종목 코드 또는 회사명
            query: stock의 별칭 (stock이 없으면 사용)
            overwrite: 캐시를 무시하고 새로 가져올지 여부
            attribute_name_str: 특정 attribute만 가져올 경우 (예: 'income_stmt', 'balance_sheet')

        Returns:
            dict: {
                "ticker": str,
                "country": str,
                "balance_sheet": str | None,  # JSON 문자열
                "income_statement": str | None,  # JSON 문자열
                "cash_flow": str | None  # JSON 문자열
            }
        """
        identifier = stock or query
        if not identifier:
            raise ValueError("Must provide either 'stock' or 'query'.")

        ticker_symbol = find.get_ticker(identifier) or identifier.upper()

        # --- 특정 attribute만 요청하는 경우 (기존 호환성 유지) ---
        if attribute_name_str:
            ticker = yf.Ticker(ticker_symbol)
            if hasattr(ticker, attribute_name_str):
                data = getattr(ticker, attribute_name_str)
                if isinstance(data, pd.DataFrame):
                    return json.loads(data.to_json(orient="records", date_format="iso"))
                if isinstance(data, pd.Series):
                    return data.to_dict()
                if isinstance(data, dict):
                    return data
                return data
            else:
                raise ValueError(f"'{attribute_name_str}' is not a valid yfinance Ticker attribute.")

        # yfinance Ticker 객체 생성
        ticker = yf.Ticker(ticker_symbol)

        # 국가 정보 추론
        country = "Unknown"
        try:
            info = ticker.info or {}
            country = info.get("country") or "Unknown"
        except Exception as e:
            logging.warning(f"Failed to fetch ticker info for {ticker_symbol}: {e}")

        # 한국 종목 코드 패턴 확인
        if ".KS" in ticker_symbol or ".KQ" in ticker_symbol:
            country = "KR"
        elif ticker_symbol.replace(".KS", "").replace(".KQ", "").isdigit() and len(ticker_symbol.replace(".KS", "").replace(".KQ", "")) == 6:
            country = "KR"

        # 재무제표 3종 수집
        result = {
            "ticker": ticker_symbol,
            "country": country,
            "balance_sheet": None,
            "income_statement": None,
            "cash_flow": None
        }

        # 1. Balance Sheet (재무상태표)
        try:
            balance_sheet = ticker.balance_sheet
            if balance_sheet is not None and not balance_sheet.empty:
                result["balance_sheet"] = balance_sheet.to_json(orient="columns", date_format="iso")
        except Exception as e:
            logging.warning(f"Failed to fetch balance_sheet for {ticker_symbol}: {e}")

        # 2. Income Statement (손익계산서)
        try:
            income_stmt = ticker.income_stmt
            if income_stmt is not None and not income_stmt.empty:
                result["income_statement"] = income_stmt.to_json(orient="columns", date_format="iso")
        except Exception as e:
            logging.warning(f"Failed to fetch income_stmt for {ticker_symbol}: {e}")

        # 3. Cash Flow (현금흐름표)
        try:
            cashflow = ticker.cashflow
            if cashflow is not None and not cashflow.empty:
                result["cash_flow"] = cashflow.to_json(orient="columns", date_format="iso")
        except Exception as e:
            logging.warning(f"Failed to fetch cashflow for {ticker_symbol}: {e}")

        # GCS에 캐시 저장
        try:
            payload_json = json.dumps(result, ensure_ascii=False, indent=2)
            self.gcs_manager.upload_file(
                source_file=payload_json,
                destination_blob_name=gcs_blob_name,
                encoding="utf-8",
                content_type="application/json; charset=utf-8",
            )
            logging.info(f"Successfully cached fundamentals for {ticker_symbol} to GCS: {gcs_blob_name}")
        except Exception as e:
            logging.error(f"GCS cache write failed for {ticker_symbol}: {e}")

        return result