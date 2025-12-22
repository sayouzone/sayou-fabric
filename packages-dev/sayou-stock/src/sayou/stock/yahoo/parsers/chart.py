import logging
import pandas as pd
import yfinance as yf

from datetime import datetime, timedelta
from typing import Optional

from ..client import YahooClient
from ..utils import (
    _CHART_URL_
)
from .quote import YahooQuoteParser

logger = logging.getLogger(__name__)

class YahooChartParser:
    """
    Yahoo Finance 시세 데이터 파서
    
    - OHLCV (Open, High, Low, Close, Volume)
    - Dividends (배당금)
    - Stock Splits (주식분할)
    - Capital Gains (양도소득)
    
    Reference:
        https://github.com/ranaroussi/yfinance/blob/main/yfinance/scrapers/history.py
    """

    DEFAULT_DAYS = 180
    MAX_YEARS = 99

    def __init__(self, client: YahooClient):
        self.client = client
        self._quote_parser: Optional[YahooQuoteParser] = None

    @property
    def quote_parser(self) -> YahooQuoteParser:
        """Lazy initialization of quote parser"""
        if self._quote_parser is None:
            self._quote_parser = YahooQuoteParser(self.client)
        return self._quote_parser

    def fetch(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        include_events: bool = True,
    ) -> pd.DataFrame:
        """
        시세 데이터 조회 (OHLCV + 배당/분할)
        
        Args:
            ticker: 종목 심볼
            start_date: 시작일 (YYYY-MM-DD), 기본값 180일 전
            end_date: 종료일 (YYYY-MM-DD), 기본값 오늘
            include_events: 배당/분할 데이터 포함 여부
        
        Returns:
            DataFrame with columns: date, open, high, low, close, volume, 
                                   [Dividends, Stock Splits, Capital Gains]
        """
        if not ticker:
            raise ValueError("Ticker symbol must be provided.")

        ticker_info = self.quote_parser.fetch(ticker)
        start_date, end_date = self._normalize_dates(start_date, end_date)

        # API 호출
        data = self._fetch_chart_data(ticker, start_date, end_date)

        if not data:
            return pd.DataFrame()

        chart = data.get('chart', {}).get('result', [])[0]

        if not chart:
            return pd.DataFrame()

        # Metadata 추출
        history_metadata = chart.get('meta', {})
        inst_type = history_metadata.get("instrumentType")
        is_mutualfund_or_etf = inst_type in ["MUTUALFUND", "ETF"]
        tz_exchange = history_metadata.get("exchangeTimezoneName")
        currency = history_metadata.get("currency")

        # OHLCV 파싱
        df = self._parse_ohlcv(chart)

        if df.empty:
            return pd.DataFrame()

        # 이벤트 데이터 병합 (배당, 분할, 양도소득)
        if include_events:
            df = self._merge_events(df, chart)

        return df
    
    def dividends(self, ticker: str):
        """배당금 내역 조회"""
        return self._fetch_event_series(ticker, "Dividends")

    def capital_gains(self, ticker: str):
        """양도소득 내역 조회"""
        return self._fetch_event_series(ticker, "Capital Gains")

    def splits(self, ticker: str):
        """주식분할 내역 조회"""
        return self._fetch_event_series(ticker, "Stock Splits")

    def fetch_with_yfinance(self, ticker: str, start_date: str | None = None, end_date: str | None = None) -> pd.DataFrame:
        """
        Yahoo Finance로부터 시세 정보를 가져와서 프론트엔드 형식에 맞게 정제하여 반환합니다.
        """
        if not ticker:
            raise ValueError("Ticker symbol must be provided.")

        ticker_info = yf.Ticker(ticker).info

        # 1. 날짜 설정
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')

        # 2. yfinance에서 데이터 가져오기
        hist_df = yf.Ticker(ticker).history(start=start_date, end=end_date)

        if hist_df.empty:
            return
            
        # 3. 가져온 데이터 BigQuery에 저장
        hist_df.reset_index(inplace=True)
        hist_df['code'] = ticker
        hist_df['source'] = 'yahoo'
        
        hist_df.rename(columns={
            'Date': 'date', 'Open': 'open', 'High': 'high', 'Low': 'low',
            'Close': 'close', 'Volume': 'volume'
        }, inplace=True)

        hist_df['date'] = pd.to_datetime(hist_df['date']).dt.date
        required_cols = ['date', 'code', 'source', 'open', 'high', 'low', 'close', 'volume']
        hist_df = hist_df[required_cols]

        for col in ['open', 'high', 'low', 'close']:
            hist_df[col] = hist_df[col].round(4)
        hist_df['volume'] = hist_df['volume'].astype('int64')

        return hist_df

    # ==================== Private Methods ====================

    def _normalize_dates(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> tuple[str, str]:
        """날짜 정규화"""
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=self.DEFAULT_DAYS)).strftime("%Y-%m-%d")
        return start_date, end_date

    def _fetch_chart_data(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
    ) -> dict:
        """Chart API 호출"""
        url = f"{_CHART_URL_}/{ticker}"
        params = {
            'period1': int(datetime.strptime(start_date, '%Y-%m-%d').timestamp()),
            'period2': int(datetime.strptime(end_date, '%Y-%m-%d').timestamp()),
            'interval': '1d',
            'events': 'div,splits,capitalGains',
            #'includeAdjustedClose': 'true',
        }

        try:
            response = self.client._get(url, params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch chart data for {ticker}: {e}")
            return {}
    
    def _parse_ohlcv(self, chart: dict) -> pd.DataFrame:
        """OHLCV 데이터 파싱"""
        timestamps = chart.get("timestamp", [])

        if not timestamps:
            return pd.DataFrame()
        
        quote = chart.get("indicators", {}).get("quote", [{}])[0]
        
        ohlcv_df = pd.DataFrame({
            "date": pd.to_datetime(timestamps, unit="s").date,
            "open": quote.get("open"),
            "high": quote.get("high"),
            "low": quote.get("low"),
            "close": quote.get("close"),
            "volume": quote.get("volume"),
        })

        print(ohlcv_df)

        # 데이터 정리
        for col in ["open", "high", "low", "close"]:
            if col in ohlcv_df.columns:
                ohlcv_df[col] = pd.to_numeric(ohlcv_df[col], errors="coerce").round(4)
        
        if "volume" in ohlcv_df.columns:
            ohlcv_df["volume"] = pd.to_numeric(ohlcv_df["volume"], errors="coerce").fillna(0).astype("int64")

        return ohlcv_df

    def _merge_events(self, df: pd.DataFrame, chart: dict) -> pd.DataFrame:
        """이벤트 데이터 (배당, 분할, 양도소득) 병합"""
        events = chart.get("events", {})
        
        # 배당금
        dividends = self._parse_event(events.get("dividends"), "Dividends", "amount")
        if not dividends.empty:
            df = self._merge_event_df(df, dividends)

        # 주식분할
        splits = self._parse_splits(events.get("splits"))
        if not splits.empty:
            df = self._merge_event_df(df, splits)

        # 양도소득
        capital_gains = self._parse_event(events.get("capitalGains"), "Capital Gains", "amount")
        if not capital_gains.empty:
            df = self._merge_event_df(df, capital_gains)

        return df

    def _parse_event(
        self,
        event_data: Optional[dict],
        column_name: str,
        value_key: str,
    ) -> pd.DataFrame:
        """이벤트 데이터 파싱 (배당금, 양도소득)"""
        if not event_data:
            return pd.DataFrame()

        df = pd.DataFrame(list(event_data.values()))
        
        if df.empty or "date" not in df.columns:
            return pd.DataFrame()

        df["date"] = pd.to_datetime(df["date"], unit="s").dt.normalize()
        df = df[["date", value_key]].rename(columns={value_key: column_name})
        
        return df.sort_values("date").reset_index(drop=True)

    def _parse_splits(self, splits_data: Optional[dict]) -> pd.DataFrame:
        """주식분할 데이터 파싱"""
        if not splits_data:
            return pd.DataFrame()

        df = pd.DataFrame(list(splits_data.values()))
        
        if df.empty or "date" not in df.columns:
            return pd.DataFrame()

        df["date"] = pd.to_datetime(df["date"], unit="s").dt.normalize()
        df["Stock Splits"] = df["numerator"] / df["denominator"]
        df = df[["date", "Stock Splits"]]
        
        return df.sort_values("date").reset_index(drop=True)

    def _merge_event_df(self, df: pd.DataFrame, event_df: pd.DataFrame) -> pd.DataFrame:
        """이벤트 DataFrame을 OHLCV에 병합"""
        if event_df.empty:
            return df

        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        
        # 병합
        df = df.merge(event_df, on="date", how="left")
        
        # 이벤트 컬럼 NaN → 0
        event_col = [c for c in event_df.columns if c != "date"][0]
        df[event_col] = df[event_col].fillna(0)

        return df

    def _fetch_event_series(self, ticker: str, column: str) -> pd.Series:
        """특정 이벤트 컬럼만 조회"""
        start_date = (datetime.now() - timedelta(days=self.MAX_YEARS * 365)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        df = self.fetch(ticker, start_date=start_date, end_date=end_date)
        
        if column not in df.columns:
            return pd.Series(dtype=float)

        # 0이 아닌 값만 반환
        series = df.set_index("date")[column]
        return series[series != 0]

    # ==================== Response Formatting ====================

    def format_response(
        self,
        df: pd.DataFrame,
        ticker: str,
        ticker_info: Optional[dict] = None,
    ) -> dict:
        """
        DataFrame을 프론트엔드 응답 형식으로 변환
        
        Returns:
            {
                "name": str,
                "source": "yahoo",
                "currentPrice": {"value": float, "changePercent": float},
                "volume": {"value": int, "changePercent": float},
                "marketCap": {"value": int, "changePercent": float},
                "priceHistory": [{"date": str, "price": float}, ...],
                "volumeHistory": [{"date": str, "volume": int}, ...],
            }
        """
        ticker_info = ticker_info or {}
        company_name = ticker_info.get("shortName", ticker)
        market_cap = ticker_info.get("marketCap", 0)

        # 빈 데이터 처리
        if df is None or df.empty:
            logger.info(f"No data for {company_name}")
            return self._empty_response(company_name, market_cap)

        # 컬럼명 정규화
        df = self._normalize_columns(df)
        df = df.sort_values("date", ascending=False).reset_index(drop=True)

        # 현재가/거래량 변동률 계산
        latest = df.iloc[0]
        previous = df.iloc[1] if len(df) > 1 else latest

        price_change = self._calc_change_percent(latest["close"], previous["close"])
        volume_change = self._calc_change_percent(latest["volume"], previous["volume"])

        return {
            "name": company_name,
            "source": "yahoo",
            "currentPrice": {
                "value": float(latest["close"]) if pd.notna(latest["close"]) else 0.0,
                "changePercent": round(price_change, 2),
            },
            "volume": {
                "value": int(latest["volume"]) if pd.notna(latest["volume"]) else 0,
                "changePercent": round(volume_change, 2),
            },
            "marketCap": {
                "value": market_cap,
                "changePercent": 0,
            },
            "priceHistory": self._format_history(df, "close", "price"),
            "volumeHistory": self._format_history(df, "volume", "volume"),
        }

    def _empty_response(self, name: str, market_cap: int) -> dict:
        """빈 응답 생성"""
        return {
            "name": name,
            "source": "yahoo",
            "currentPrice": {"value": 0, "changePercent": 0},
            "volume": {"value": 0, "changePercent": 0},
            "marketCap": {"value": market_cap, "changePercent": 0},
            "priceHistory": [],
            "volumeHistory": [],
        }

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """컬럼명 정규화"""
        df = df.copy()
        
        if "date" not in df.columns:
            df = df.reset_index()
        
        rename_map = {
            "Date": "date",
            "Close": "close",
            "Volume": "volume",
            "Open": "open",
            "High": "high",
            "Low": "low",
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
        
        return df

    @staticmethod
    def _calc_change_percent(current: float, previous: float) -> float:
        """변동률 계산"""
        if not previous or previous == 0:
            return 0.0
        return ((current - previous) / previous) * 100

    @staticmethod
    def _timestamp_to_date(timestamp: int):
        """Unix timestamp를 date로 변환"""
        if not timestamp:
            return None
        try:
            return datetime.fromtimestamp(timestamp).date()
        except (ValueError, TypeError, OSError):
            return None

    def _format_history(
        self,
        df: pd.DataFrame,
        source_col: str,
        target_col: str,
    ) -> list[dict]:
        """히스토리 데이터 포맷팅"""
        history = []
        
        for _, row in df.iterrows():
            date_val = row["date"]
            if isinstance(date_val, (pd.Timestamp, datetime)):
                date_str = pd.to_datetime(date_val).strftime("%Y-%m-%d")
            else:
                date_str = str(date_val)

            value = row[source_col]
            if target_col == "volume":
                value = int(value) if pd.notna(value) else 0
            else:
                value = float(value) if pd.notna(value) else 0.0

            history.append({"date": date_str, target_col: value})

        return history