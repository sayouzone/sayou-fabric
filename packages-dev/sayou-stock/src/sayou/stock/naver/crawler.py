from .client import NaverClient
#from .models import DartConfig

from .parsers import (
    NaverNewsParser,
    NaverMarketParser,
)

class NaverCrawler:
        
    """Naver 뉴스/시세 크롤러."""
    
    def __init__(self, client_id: str = None, client_secret: str = None):
        """크롤러를 초기화합니다."""
        self.client = NaverClient()

        # 파서 초기화
        self._news_parser = NaverNewsParser(self.client, client_id, client_secret)
        self._market_parser = NaverMarketParser(self.client)

    def main(self, stock: str):
        return self._main_parser.parse(stock)

    def market(self, stock: str, start_date: str = None, end_date: str = None):
        return self._market_parser.fetch(stock, start_date=start_date, end_date=end_date)

    def main_prices(self, stock: str):
        return self._market_parser.fetch_main_prices(stock)

    def company_metadata(self, stock: str):
        return self._market_parser.fetch_company_metadata(stock)

    def news(self, query: str, max_articles: int = 100):
        news_list = self._news_parser.fetch(query=query, max_articles=max_articles)

        return self._news_parser.parse(news_list)

    def category_news(self):
        return self._news_parser.fetch(category="카테고리")