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
 
"""
Kisrating Crawler
===========================

Kisrating에서 주요 데이터를 추출하는 Python 패키지

Installation:
    pip install requests beautifulsoup4 lxml

Quick Start:
    >>> from naver import NaverCrawler
    >>> 
    >>> client_id = "your_client_id"
    >>> client_secret = "your_client_secret"
    >>> crawler = NaverCrawler(client_id, client_secret)
    >>> 
    >>> # Naver 일별 시세 조회
    >>> start_date='2025-01-01'
    >>> end_date='2025-12-31'
    >>> data = crawler.market(code, start_date=start_date, end_date=end_date)
    >>> print(data)
    >>> 
    >>> # Naver 주요 시세 조회
    >>> df_main_prices = crawler.main_prices(code)
    >>> print(df_main_prices)
    >>> 
    >>> # Naver 기업 정보 조회
    >>> metadata = crawler.company_metadata(code)
    >>> print(metadata)
    >>> 
    >>> # Naver 뉴스 카테고리별 검색
    >>> articles = crawler.category_news()
    >>> print(articles)
    >>> 
    >>> # Naver 뉴스 검색
    >>> articles = crawler.news(query="삼성전자", display=10)
    >>> print(articles)

Supported Filings:
    - Naver 일별 시세 조회
    - Naver 주요 시세 조회
    - Naver 기업 정보 조회
    - Naver 뉴스 카테고리별 검색
    - Naver 뉴스 검색

Note:
    Naver에서 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET 환경 변수를 설정하세요.
"""

__version__ = "0.1.0"
__author__ = "SeongJung Kim"

from .crawler import KisratingCrawler
from .client import KisratingClient
from .models import (
    # Finance
    Statistics,
)
from .parsers import (
    StatisticsParser,
)

__all__ = [
    # 메인 클래스
    "KisratingCrawler",
    "KisratingClient",
    
    # 데이터 모델
    # Finance
    "Statistics",
    
    # 파서
    "StatisticsParser",
]
