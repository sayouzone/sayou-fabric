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
import random
import time

from bs4 import BeautifulSoup, Tag
from typing import Dict, Any, List, Tuple, Optional
from urllib import parse

from ..client import NaverClient
from ..models import NewsArticle, NewsSearchResult
from ..utils import (
    NEWS_BASE_URL,
    NEWS_URLS,
    FINANCE_URL,
    FINANCE_API_URL,
    NEWS_SELECTORS,
    NEWS_TITLE_SELECTORS,
    NEWS_CONTENT_SELECTORS,
    NEWS_AUTHORS_SELECTORS,
    NEWS_PUBLISHED_DATE_SELECTORS,
    NEWS_PRESS_SELECTORS,
    NEWS_CATEGORY_SELECTORS,
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NaverNewsParser:
    """
    뉴스 파서 클래스
    
    Attributes:
        client: NaverClient 인스턴스
        client_id: Naver API Client ID
        client_secret: Naver API Client Secret
        max_per_category: 카테고리별 최대 기사 수
    """

    DEFAULT_MAX_PER_CATEGORY = 10
    DEFAULT_DELAY_RANGE = (0.1, 0.3)
    
    def __init__(
        self, 
        client: NaverClient, 
        client_id: str, 
        client_secret: str,
        max_per_category: int = DEFAULT_MAX_PER_CATEGORY
    ):
        self.client = client
        self.client_id = client_id
        self.client_secret = client_secret
        self.max_per_category = max_per_category

        self._detail_parser = NaverNewsDetailParser(client)

    def fetch(
        self,
        category: str = "조회",
        query: Optional[str] = None,
        url: Optional[str] = None,
        max_articles: int = 100
    ) -> List[Dict]:
        """
        질문으로 Naver News API를 뉴스 목록을 조회한다.
        카테고리에 대한 뉴스 목록을 조회한다.
        
        Args:
            ategory: 조회 모드 또는 카테고리명 (정치, 경제, 사회, 생활/문화, IT/과학, 세계)
            query: 검색어 (category가 "조회"일 때 사용)
            url: 커스텀 API URL
            max_articles: 최대 기사 수

        Returns:
            NewsArticle 목록
        """

        if category != "조회":
            return self._fetch_category_news()
        
        url = NEWS_URLS.get("openapi") if not url else url
        enc_text = parse.quote(query)
        #api_url = url.format(query=enc_text, display=max_articles)

        params = {
            "query": enc_text,
            "display": max_articles
        }
        
        api_headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }

        articles = []
        try:
            logger.info(f"News 목록 URL: {url}, params: {params}")
            response = self.client._get(url, params=params, headers=api_headers)
            search_result = response.json()

            # JSON에서 link 정보 추출
            news_list = search_result.get('items', [])
            #print(f"Items: {news_list}")
            for item in news_list:
                article = NewsArticle(
                    url=item.get("link"),
                    query=query,
                    title=item.get("title")
                )
                articles.append(article)
            
            return articles
        except Exception as e:
            print(f"Exception: 뉴스 검색 실패 {e}")
        
        return articles

    def parse(
        self,
        articles: List[Dict],
        delay_range: tuple = DEFAULT_DELAY_RANGE
    ) -> List[NewsArticle]:
        """
        뉴스 목록의 상세 정보를 파싱한다.
        제목, 내용, 언론사, 입력일, 기자 목록
        카테고리 X

        Args:
            articles: NewsArticle 목록
            delay_range: 요청 간 지연 시간 범위 (초)

        Returns:
            상세 정보가 채워진 NewsArticle 목록
        """

        for article in articles:
            if article.is_naver_news:
                self._detail_parser.fetch(article)
                time.sleep(random.uniform(*delay_range))

        return articles

    def _fetch_category_news(self) -> List[NewsArticle]:
        """
        카테고리별 뉴스 목록을 가져온다.
        """
        articles = []

        for category_name, category_url in NEWS_URLS.items():
            if category_name == "openapi":
                continue
            logger.info(f"News 목록 URL: {category_url}")
            category_articles = self._fetch_articles_from_category(
                category_name, category_url
            )
            articles.extend(category_articles)

        return articles

    def _fetch_articles_from_category(
        self,
        category_name: str,
        category_url: str,
    ) -> List[NewsArticle]:
        """특정 카테고리에서 기사 목록 추출"""
        articles = []

        try:
            response = self.client._get(
                category_url,
                referer=NEWS_BASE_URL,
                timeout=30,
            )
            soup = BeautifulSoup(response.text, "html.parser")

            for selector in NEWS_SELECTORS:
                elements = soup.select(selector)

                for element in elements:
                    url = element.get("href")

                    if self._is_valid_article_url(url):
                        article = NewsArticle(
                            url=url,
                            query=category_name,
                            title=element.get_text(strip=True),
                        )
                        articles.append(article)

                        if len(articles) >= self.max_per_category:
                            break

                if len(articles) >= self.max_per_category:
                    break

            logger.info(f"✅ {len(articles)}개의 기사 링크 수집 완료")

        except Exception as e:
            logger.error(f"기사 링크 수집 실패: {e}")

        return articles[: self.max_per_category]

    @staticmethod
    def _is_valid_article_url(url: Optional[str]) -> bool:
        """유효한 기사 URL인지 확인"""
        if not url:
            return False
        return (
            "news.naver.com" in url
            and "/article/" in url
            and "/comment/" not in url
        )

class NaverNewsDetailParser:
    """
    뉴스 상세 정보 파서
    
    Attributes:
        client: NaverClient 인스턴스
    """

    DEFAULT_TITLE = "제목 없음"
    DEFAULT_CONTENT = "본문 없음"
    DEFAULT_PRESS = "언론사 불명"
    
    def __init__(
        self,
        client: NaverClient
    ):
        self.client = client

    def fetch(
        self,
        article: NewsArticle
    ):
        """
        뉴스 상세 정보를 가져와서 article 객체를 업데이트한다.
        
        Args:
            article: NewsArticle 인스턴스

        Returns:
            업데이트된 NewsArticle
        """        
        try:
            logger.info(f"News Detail URL: {article.url}")
            response = self.client._get(article.url)

            # 뉴스 상세 정보 파싱
            self._parse_and_update(article, response.text)

        except Exception as e:
            logger.error(f"Error scraping {article.url}: {e}")

        finally:
            return article

    def _parse_and_update(
        self,
        article: NewsArticle,
        html_text: str
    ) -> None:
        """
        HTML에서 뉴스 상세 정보를 파싱한다.
        제목, 본문 내용, 언론사, 입력일, 기자 목록

        Args:
            html_text (str): HTML 텍스트

        Returns:
            뉴스 상세 Dictionary
        """
        soup = BeautifulSoup(html_text, 'html.parser')

        article.update_detail(
            title=self._parse_title(soup),
            content=self._parse_content(soup),
            press=self._parse_press(soup),
            authors=self._parse_authors(soup),
            category=self._parse_category(soup),
            published_date=self._parse_published_date(soup),
        )

    def _parse_title(
        self,
        soup: BeautifulSoup
    ) -> str:
        """
        HTML에서 제목을 파싱한다.

        Args:
            soup:

        Returns:
            제목 문자열
        """        
        for selector in NEWS_TITLE_SELECTORS:
            try:
                element = soup.select_one(selector)
                if element:
                    return element.get_text(strip=True)
            except:
                continue

        return self.DEFAULT_TITLE

    def _parse_content(
        self,
        soup: BeautifulSoup
    ) -> str:
        """
        HTML에서 본문 내용을 파싱한다.

        Args:
            soup:

        Returns:
            본문 내용 문자열
        """        
        for selector in NEWS_CONTENT_SELECTORS:
            try:
                element = soup.select_one(selector)
                if element:
                    return element.get_text(strip=True)
            except:
                continue

        return self.DEFAULT_CONTENT

    def _parse_press(
        self,
        soup: BeautifulSoup
    ) -> str:
        """
        HTML에서 언론사를 파싱한다.

        Args:
            soup:

        Returns:
            언론사 문자열
        """

        for selector, attr in NEWS_PRESS_SELECTORS:
            try:
                element = soup.select_one(selector)
                if element:
                    return element.get(attr, self.DEFAULT_PRESS)
            except:
                continue

        return self.DEFAULT_PRESS

    def _parse_published_date(
        self,
        soup
    ) -> str:
        """
        HTML에서 뉴스 입력일을 파싱한다.

        Args:
            soup:

        Returns:
            뉴스 입력일 문자열
        """

        for selector, attr in NEWS_PUBLISHED_DATE_SELECTORS:
            try:
                element = soup.select_one(selector)
                if element:
                    return element.get(attr, '')
            except:
                continue
        
        return datetime.now().strftime('%Y-%m-%d %H:%M')

    def _parse_authors(
        self,
        soup: BeautifulSoup
    ) -> List:
        """
        HTML에서 기자 목록을 파싱한다.

        Args:
            soup:

        Returns:
            기자 목록
        """
        authors = []
        
        for selector in NEWS_AUTHORS_SELECTORS:
            try:
                elements = soup.select(selector)
                for element in elements:
                    author = element.get_text(strip=True)
                    if author:
                        authors.append(author)
            except Exception as e:
                logger.warning(f"Error parsing authors: {e}")
                continue
        
        return authors
    
    def _parse_category(
        self,
        soup: BeautifulSoup
    ) -> Optional[str]:
        """
        HTML에서 카테고리를 파싱한다.

        Args:
            soup:

        Returns:
            카테고리
        """
        
        for selector in NEWS_CATEGORY_SELECTORS:
            try:
                element = soup.select_one(selector)
                if element:
                    return element.get_text(strip=True)
            except Exception as e:
                logger.warning(f"Error parsing category: {e}")
                continue
        
        return None