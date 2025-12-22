import logging
import pandas as pd
import random
import time
import yfinance as yf

from bs4 import BeautifulSoup, Tag
from datetime import datetime, timedelta

from ..client import YahooClient
from ..utils import (
    _QUERY2_URL_,
    _QUOTE_SUMMARY_URL_,
    _NEWS_URL_
)

logger = logging.getLogger(__name__)

class YahooNewsParser:
    """
    Yahoo Finance API 파싱 클래스
    
    뉴스: 
    """

    # 크롤링 차단하는 도메인 목록
    BLOCKED_DOMAINS = [
        "thestreet.com",
        "barrons.com",
        "wsj.com",
        "bloomberg.com",
        "ft.com",
        "seekingalpha.com",
    ]

    QUERY_REFS = {
        "all": "newsAll",
        "news": "latestNews",
        "press releases": "pressRelease",
    }

    # Rename for compatibility
    RENAME_MAP = {
        "pubDate": "providerPublishTime",
        "content_pubDate": "providerPublishTime",
        "canonicalUrl.url": "link",
        "content_canonicalUrl_url": "link",
    }

    def __init__(self, client: YahooClient):
        self.client = client

    def fetch(
        self,
        query: str,
        max_articles: int = 100,
        period: str = "7",
        fetch_content: bool = False,
        tab: str = "news",
    ) -> pd.DataFrame:
        """
        회사 이름(query)을 받아서 티커로 변환한 뒤,
        Yahoo Finance에서 뉴스를 수집하고, 기사 본문을 크롤링합니다.

        Args:
            query (str): 회사 이름
            max_articles (int, optional): 최대 기사 수. Defaults to 100.
            period (str, optional): 기간. Defaults to "7".
            fetch_content (bool, optional): 상세 정보 여부. Defaults to False.
        Returns:
            pd.DataFrame: 뉴스 데이터프레임
        """

        ticker = query

        query_ref = self.QUERY_REFS.get(tab.lower())
        if not query_ref:
            raise ValueError(f"Invalid tab name '{tab}'. Choose from: {', '.join(self.QUERY_REFS.keys())}")

        news_list = self._fetch_with_requests(query, query_ref, max_articles)
        if not news_list:
            logger.info(f"No news found for {query}")
            return pd.DataFrame()
        
        if max_articles is not None:
            news_list = news_list[:max_articles]

        articles = self._fetch_detail(news_list) if fetch_content else news_list
        
        df = pd.json_normalize(articles)
        return self._finalize_dataframe(df, query, period)
    
    def _fetch_with_requests(self, ticker: str, query_ref: str, max_articles: int) -> list[dict]:
        """Yahoo Finance에서 requests를 사용해서 뉴스 목록 크롤링"""

        params = { 
            "queryRef": query_ref,
            "serviceKey": "ncp_fin"
        }

        payload = {
            "serviceConfig": {
                "snippetCount": max_articles,
                "s": [ticker]
            }
        }
        
        try:
            response = self.client._post(_NEWS_URL_, params=params, body=payload, timeout=10)
            data = response.json()
            status = data.get('status')
            stream = data.get("data", {}).get("tickerStream", {}).get("stream", [])
            return [item.get("content", {}) for item in stream][:max_articles]
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return []

    def _fetch_detail(self, news_list: list) -> str | None:
        articles = []

        total_articles = len(news_list)
        for i, item in enumerate(news_list):
            print(item)
            link = item.get('canonicalUrl', {}).get('url')
            item['crawled_content'] = None # Initialize to None
            if link:
                item['crawled_content'] = self._fetch_content(link)
            articles.append(item)
        
        return articles

    def fetch_with_yfinance(
        self,
        query: str,
        max_articles: int = 100,
        period: str = "7",
    ) -> pd.DataFrame:
        """
        회사 이름(query)을 받아서 티커로 변환한 뒤,
        Yahoo Finance에서 뉴스를 수집하고, 기사 본문을 크롤링합니다.
        """

        ticker = query
        news_list = yf.Ticker(ticker).news

        if not news_list:
            return pd.DataFrame()
        
        if max_articles is not None:
            news_list = news_list[:max_articles]
                
        articles = []
        total_articles = len(news_list)
        for i, item in enumerate(news_list):
            print(item)
            link = item.get('content', {}).get('canonicalUrl', {}).get('url')
            print(link)
            item['crawled_content'] = None # Initialize to None
            if link:
                item['crawled_content'] = self._fetch_content(link)
            articles.append(item)
        
        df = pd.json_normalize(articles)
        return self._finalize_dataframe(df, query, period)

    def _fetch_content(self, url: str) -> str | None:
        """
        URL을 받아 웹 페이지의 본문 텍스트를 크롤링합니다.
        """

        # 차단 도메인 스킵
        if any(domain in url for domain in self.BLOCKED_DOMAINS):
            return None

        # 요청 간 딜레이
        time.sleep(random.uniform(0.5, 1.5))

        response = self.client._get(url)

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text

    def _finalize_dataframe(self, df: pd.DataFrame, query: str, period: str) -> pd.DataFrame:
        if df.empty:
            return df

        df.rename(columns={k: v for k, v in self.RENAME_MAP.items() if k in df.columns}, inplace=True)

        # Add additional metadata
        df['search_keyword'] = query
        df['crawled_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Convert publish time to datetime and then to string
        if 'providerPublishTime' in df.columns:
            df['providerPublishTime'] = pd.to_datetime(df['providerPublishTime']).dt.strftime('%Y-%m-%d %H:%M:%S')

        # Reorder columns to have crawled_content at the end
        if 'crawled_content' in df.columns:
            cols = df.columns.tolist()
            cols.remove('crawled_content')
            cols.append('crawled_content')
            df = df[cols]

        if 'providerPublishTime' in df.columns:
            period_days = int(period)
            cutoff_date = datetime.now() - timedelta(days=period_days)
            df = df[pd.to_datetime(df['providerPublishTime']) >= cutoff_date]

        return df