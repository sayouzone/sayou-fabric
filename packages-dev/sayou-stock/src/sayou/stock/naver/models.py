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
Naver News Data Models

뉴스 데이터를 표현하는 데이터 클래스 모듈
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional

@dataclass
class NewsArticle:
    """
    뉴스 기사 데이터 모델
    
    Attributes:
        url: 기사 URL
        query: 검색어 또는 카테고리명
        title: 기사 제목
        content: 본문 내용
        press: 언론사
        authors: 기자 목록 (콤마 구분 문자열)
        category: 카테고리
        published_date: 기사 입력일
        crawled_at: 크롤링 시각
    """
    url: str
    query: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    press: Optional[str] = None
    authors: Optional[str] = None
    category: Optional[str] = None
    published_date: Optional[str] = None
    crawled_at: Optional[str] = None

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "NewsArticle":
        """딕셔너리에서 생성"""
        return cls(
            url=data.get("url", ""),
            query=data.get("query"),
            title=data.get("title"),
            content=data.get("content"),
            press=data.get("press"),
            authors=data.get("authors"),
            category=data.get("category"),
            published_date=data.get("published_date"),
            crawled_at=data.get("crawled_at"),
        )

    def update_detail(
        self,
        title: str,
        content: str,
        press: str,
        authors: List[str],
        category: str,
        published_date: str,
    ) -> None:
        """상세 정보 업데이트"""
        self.title = title
        self.content = content
        self.press = press
        self.authors = ", ".join(authors) if authors else None
        self.category = category
        self.published_date = published_date
        self.crawled_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @property
    def is_naver_news(self) -> bool:
        """네이버 뉴스 URL인지 확인"""
        return self.url is not None and "news.naver.com" in self.url

    @property
    def has_detail(self) -> bool:
        """상세 정보가 있는지 확인"""
        return self.content is not None and self.content != "본문 없음"


@dataclass
class NewsSearchResult:
    """
    뉴스 검색 결과 모델
    
    Attributes:
        query: 검색어
        total_count: 총 검색 결과 수
        articles: 기사 목록
        searched_at: 검색 시각
    """
    query: str
    articles: List[NewsArticle] = field(default_factory=list)
    total_count: int = 0
    searched_at: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "query": self.query,
            "total_count": self.total_count,
            "searched_at": self.searched_at,
            "articles": [article.to_dict() for article in self.articles],
        }

    def add_article(self, article: NewsArticle) -> None:
        """기사 추가"""
        self.articles.append(article)
        self.total_count = len(self.articles)


@dataclass
class CategoryNews:
    """
    카테고리별 뉴스 모델
    
    Attributes:
        category: 카테고리명
        url: 카테고리 URL
        articles: 기사 목록
    """
    category: str
    url: str
    articles: List[NewsArticle] = field(default_factory=list)

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "category": self.category,
            "url": self.url,
            "articles": [article.to_dict() for article in self.articles],
        }