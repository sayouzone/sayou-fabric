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
        Yahoo Finance로부터 시세 정보를 가져와서 정제하여 반환합니다.

        Args:
            ticker (str): 티커 심볼
            start_date (str | None, optional): 시작 날짜. Defaults to None.
            end_date (str | None, optional): 종료 날짜. Defaults to None.
        Returns:
            pd.DataFrame: 정제된 OHLCV(open, high, low, close, volume) 데이터
        """
        if not ticker:
            raise ValueError("Ticker symbol must be provided.")

        quote_parser = YahooQuoteParser(self.client)
        ticker_info = quote_parser.fetch(ticker)

        # 1. 날짜 설정
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')

        url = f"{_CHART_URL_}/{ticker}"
        params = {
            'period1': int(datetime.strptime(start_date, '%Y-%m-%d').timestamp()),
            'period2': int(datetime.strptime(end_date, '%Y-%m-%d').timestamp()),
            'interval': '1d',
            'events': 'div,splits,capitalGains',
            #'includeAdjustedClose': 'true',
        }

        # 2. Yahoo Finance에서 데이터 가져오기
        response = self.client._get(url, params=params)
        data = response.json()
        #print(data)

        if not data or 'chart' not in data or 'result' not in data['chart'] or not data['chart']['result']:
            return pd.DataFrame()

        result = data.get('chart', {}).get('result', [])
        if not result:
            return pd.DataFrame()

        chart = result[0]
        
        # Metadata 추출
        history_metadata = chart.get('meta', {})
        inst_type = history_metadata.get("instrumentType")
        is_mutualfund_or_etf = inst_type in ["MUTUALFUND", "ETF"]
        tz_exchange = history_metadata.get("exchangeTimezoneName")
        currency = history_metadata.get("currency")

        # Timestamp 추출
        timestamps = chart.get('timestamp', [])
        
        # Quote, Adjusted Close 추출
        quote = chart.get('indicators', {}).get("quote", [{}])[0]
        #adjclose = chart.get('indicators', {}).get("adjclose", [{}])[0]

        hist_df = pd.DataFrame({
            "date": pd.to_datetime(timestamps, unit='s'),
            "open": quote.get("open", [0]),
            "high": quote.get("high", [0]),
            "low": quote.get("low", [0]),
            "close": quote.get("close", [0]),
            "volume": quote.get("volume", [0]),
            #"adjclose": adjclose.get("adjclose", [0]),   
        })
        #print(hist_df)

        if hist_df.empty:
            return pd.DataFrame()

        # 날짜만 추출 (시간 제외)
        hist_df['date'] = pd.to_datetime(hist_df['date']).dt.date
        
        #hist_df.insert(0, "symbol", metadata.get("symbol"))
        
        # 소수점 정리
        for col in ['open', 'high', 'low', 'close']:
            hist_df[col] = hist_df[col].round(4)
        # 정수로 변환
        hist_df['volume'] = hist_df['volume'].astype('int64')

        dividends, splits, capital_gains = self._events(chart)
        print(dividends)
        print(splits)
        print(capital_gains)

        if not dividends.empty:
            hist_df = self._merge_dfs(hist_df, dividends)
        if not splits.empty:
            hist_df = self._merge_dfs(hist_df, splits)
        if not capital_gains.empty:
            hist_df = self._merge_dfs(hist_df, capital_gains)

        #print(hist_df)

        return hist_df
    
    def dividends(self, ticker: str):
        """
        Yahoo Finance로부터 배당 정보를 반환합니다.
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=(99*365))).strftime('%Y-%m-%d')
        df =self.fetch(ticker, start_date=start_date, end_date=end_date)
        if "Dividends" in df:
            dividends = df["Dividends"]
            return dividends[dividends != 0]

        return pd.DataFrame()

    def capital_gains(self, ticker: str):
        """
        Yahoo Finance로부터 양도소득 (Capital Gains) 정보를 반환합니다.
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=(99*365))).strftime('%Y-%m-%d')
        df =self.fetch(ticker, start_date=start_date, end_date=end_date)
        if "CapitalGains" in df:
            capital_gains = df["CapitalGains"]
            return capital_gains[capital_gains != 0]

        return pd.DataFrame()

    def splits(self, ticker: str):
        """
        Yahoo Finance로부터 주식 분할 정보를 반환합니다.
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=(99*365))).strftime('%Y-%m-%d')
        df =self.fetch(ticker, start_date=start_date, end_date=end_date)
        if "Stock Splits" in df:
            splits = df["Stock Splits"]
            return splits[splits != 0]

        return pd.DataFrame()

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

    def _df_tz(df, tz):
        if df.index.tz in None:
            df.index = df.index.tz_localize("UTC")
        df.index = df.index.tz_convert(tz)
        return df

    def _events(self, data):
        dividends = None
        capital_gains = None
        splits = None

        if 'events' in data:
            events = data['events']
            if 'dividends' in events: 
                dividends = pd.DataFrame(
                    data=list(events['dividends'].values())
                )
                dividends.set_index("date", inplace=True)
                dividends.index = pd.to_datetime(dividends.index, unit='s')
                dividends.sort_index(inplace=True)
                dividends = dividends.rename(columns={'amount': 'Dividends'})

            if 'capitalGains' in events:
                capital_gains = pd.DataFrame(
                    data=list(events['capitalGains'].values())
                )
                capital_gains.set_index("date", inplace=True)
                capital_gains.index = pd.to_datetime(capital_gains.index, unit='s')
                capital_gains.sort_index(inplace=True)
                capital_gains.columns = ["Capital Gains"]

            if 'splits' in events:
                splits = pd.DataFrame(
                    data=list(events['splits'].values())
                )
                splits.set_index("date", inplace=True)
                splits.index = pd.to_datetime(splits.index, unit='s')
                splits.sort_index(inplace=True)
                splits["Stock Splits"] = splits["numerator"] / splits["denominator"]
                splits = splits[["Stock Splits"]]

        if dividends is None:
            dividends = pd.DataFrame(
                columns=["Dividends"], index=pd.DatetimeIndex([]))
        if capital_gains is None:
            capital_gains = pd.DataFrame(
                columns=["Capital Gains"], index=pd.DatetimeIndex([]))
        if splits is None:
            splits = pd.DataFrame(
                columns=["Stock Splits"], index=pd.DatetimeIndex([]))

        return dividends, capital_gains, splits

    def _merge_dfs(self, df: pd.DataFrame, df_sub: pd.DataFrame) -> pd.DataFrame:
        """
        OHLCV 데이터와 배당금 데이터를 병합
        
        Args:
            df: OHLCV DataFrame (date, open, high, low, close, volume)
            df_sub: 배당금 DataFrame (date index, Dividends column)
        
        Returns:
            병합된 DataFrame
        """
        if df_sub.empty:
            raise Exception("No data to merge")
        
        if df.empty:
            raise df

        columns = [col for col in df_sub.columns if col not in df]
        if len(columns) > 1:
            raise ValueError("df_sub must have only one column.")
        data_column = columns[0]

        #df = df.sort_index()
        #indices = np.searchsorted(np.append(df.index, df.index[-1] + timedelta(days=1)), df_sub.index, side='right')
        #indices -= 1  # Convert from [[i-1], [i]) to [[i], [i+1])
        
        # df의 date를 datetime으로 변환
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        
        # df_div 처리
        df_sub2 = df_sub.copy()
        columns = df_sub.columns.tolist()
        #print('columns', columns, type(columns))

        # 인덱스가 datetime인 경우 리셋
        if isinstance(df_sub2.index, pd.DatetimeIndex):
            df_sub2 = df_sub2.reset_index()
            columns.insert(0, "date")
            #print('columns', columns)
            df_sub2.columns = columns
        
        # 날짜만 추출 (시간 제거)
        df_sub2["date"] = pd.to_datetime(df_sub2["date"]).dt.normalize()
        
        # 같은 날짜에 여러 배당이 있을 경우 합산
        #df_sub2 = df_sub2.groupby("date")["dividends"].sum().reset_index()
        
        # 병합 (left join - OHLCV 기준)
        df_merged = df.merge(df_sub2, on="date", how="left")
        
        # 배당금 없는 날은 0으로 채우기
        for col in columns:
            df_merged[col] = df_merged[col].fillna(0)
        
        return df_merged

    def _format_response_from_df(self, df: pd.DataFrame, ticker_info: dict, ticker: str):
        """DataFrame을 받아 프론트엔드 응답 형식으로 변환하는 헬퍼 함수"""
        company_name = ticker_info.get('shortName', ticker)
        market_cap = ticker_info.get('marketCap', 0)

        if df is None or df.empty:
            print(f"'{company_name}'에 대한 데이터가 없어 빈 응답을 반환합니다.")
            return {
                "name": company_name,
                "source": "yahoo",
                "currentPrice": {"value": 0, "changePercent": 0},
                "volume": {"value": 0, "changePercent": 0},
                "marketCap": {"value": market_cap, "changePercent": 0},
                "priceHistory": [],
                "volumeHistory": [],
            }
        
        # BQ에서 온 데이터는 'date', 'close', 'volume' 컬럼이 존재.
        # yfinance에서 온 데이터는 'Date' 인덱스와 'Close', 'Volume' 컬럼을 가짐.
        if 'date' not in df.columns:
            df.reset_index(inplace=True)
            df.rename(columns={'Date': 'date', 'Close': 'close', 'Volume': 'volume'}, inplace=True)

        df.sort_values(by='date', ascending=False, inplace=True)
        df.reset_index(drop=True, inplace=True)

        latest = df.iloc[0]
        previous = df.iloc[1] if len(df) > 1 else latest

        price_change_percent = ((latest['close'] - previous['close']) / previous['close']) * 100 if previous['close'] != 0 else 0
        volume_change_percent = ((latest['volume'] - previous['volume']) / previous['volume']) * 100 if previous['volume'] != 0 else 0

        latest_close = float(latest['close']) if pd.notna(latest['close']) else 0.0
        latest_volume = int(latest['volume']) if pd.notna(latest['volume']) else 0

        result = {
            "name": company_name,
            "source": "yahoo",
            "currentPrice": {
                "value": latest_close,
                "changePercent": round(price_change_percent, 2)
            },
            "volume": {
                "value": latest_volume,
                "changePercent": round(volume_change_percent, 2)
            },
            "marketCap": {
                "value": market_cap,
                "changePercent": 0 
            },
            "priceHistory": df.rename(columns={'close': 'price'})[['date', 'price']].to_dict(orient='records'),
            "volumeHistory": df[['date', 'volume']].to_dict(orient='records')
        }

        for item in result['priceHistory']:
            if isinstance(item['date'], pd.Timestamp) or isinstance(item['date'], datetime.date):
                item['date'] = pd.to_datetime(item['date']).strftime('%Y-%m-%d')
            item['price'] = float(item['price'])

        for item in result['volumeHistory']:
            if isinstance(item['date'], pd.Timestamp) or isinstance(item['date'], datetime.date):
                item['date'] = pd.to_datetime(item['date']).strftime('%Y-%m-%d')
            item['volume'] = int(item['volume'])

        return result