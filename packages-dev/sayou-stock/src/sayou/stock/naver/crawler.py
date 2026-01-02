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

from .client import NaverClient

from .parsers import (
    NaverNewsParser,
    NaverMarketParser,
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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