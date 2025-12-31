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

from dataclasses import dataclass, field, asdict
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any

"""
Naver Market Data Models

주식 시장 데이터를 표현하는 데이터 클래스 모듈
"""

class Currency(Enum):
    """통화 코드"""
    KRW = "KRW"
    USD = "USD"
    JPY = "JPY"
    CNY = "CNY"
    
    @classmethod
    def from_nation_code(cls, nation_code: Optional[str]) -> Optional["Currency"]:
        """국가 코드로부터 통화 추론"""
        if not nation_code:
            return None
        
        mapping = {
            "KOR": cls.KRW, "KR": cls.KRW,
            "USA": cls.USD, "US": cls.USD,
            "JPN": cls.JPY, "JP": cls.JPY,
            "CHN": cls.CNY, "CN": cls.CNY,
        }
        return mapping.get(nation_code.upper())


class TimeFrame(Enum):
    """시세 조회 시간 단위"""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class SortOrder(Enum):
    """정렬 순서"""
    ASC = "asc"
    DESC = "desc"


@dataclass
class StockPrice:
    """
    주식 일별 시세 데이터 모델
    
    Attributes:
        date: 거래일
        open: 시가
        high: 고가
        low: 저가
        close: 종가
        volume: 거래량
        foreign_investment_rate: 외국인 소진율 (optional)
    """
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    foreign_investment_rate: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = asdict(self)
        result["date"] = self.date.strftime("%Y-%m-%d") if self.date else None
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StockPrice":
        """딕셔너리에서 생성"""
        date_val = data.get("date")
        if isinstance(date_val, str):
            date_val = datetime.strptime(date_val, "%Y-%m-%d")
        
        return cls(
            date=date_val,
            open=float(data.get("open", 0)),
            high=float(data.get("high", 0)),
            low=float(data.get("low", 0)),
            close=float(data.get("close", 0)),
            volume=int(data.get("volume", 0)),
            foreign_investment_rate=data.get("foreign_investment_rate"),
        )

    @property
    def price_change(self) -> float:
        """시가 대비 종가 변동"""
        if self.open == 0:
            return 0.0
        return self.close - self.open

    @property
    def price_change_rate(self) -> float:
        """시가 대비 종가 변동률 (%)"""
        if self.open == 0:
            return 0.0
        return ((self.close - self.open) / self.open) * 100


@dataclass
class MainPrices:
    """
    주요 시세 데이터 모델
    
    Attributes:
        current_price: 현재가
        prev_close: 전일 종가
        open_price: 시가
        high_price: 고가
        low_price: 저가
        volume: 거래량
        trading_value: 거래대금
        market_cap: 시가총액
        shares_outstanding: 상장주식수
        high_52week: 52주 최고
        low_52week: 52주 최저
        per: PER
        eps: EPS
        pbr: PBR (추정)
        dividend_yield: 배당수익률
        raw_data: 원본 데이터 (한글 키)
    """
    current_price: Optional[float] = None
    prev_close: Optional[float] = None
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    volume: Optional[int] = None
    trading_value: Optional[float] = None
    market_cap: Optional[float] = None
    shares_outstanding: Optional[int] = None
    high_52week: Optional[float] = None
    low_52week: Optional[float] = None
    per: Optional[float] = None
    eps: Optional[float] = None
    pbr: Optional[float] = None
    dividend_yield: Optional[float] = None
    raw_data: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "MainPrices":
        """원본 한글 데이터에서 생성"""
        def parse_number(value: Optional[str]) -> Optional[float]:
            if not value:
                return None
            try:
                cleaned = value.replace(",", "").replace("%", "").replace("배", "").replace("원", "")
                return float(cleaned)
            except (ValueError, AttributeError):
                return None

        def parse_int(value: Optional[str]) -> Optional[int]:
            num = parse_number(value)
            return int(num) if num is not None else None

        return cls(
            current_price=parse_number(raw_data.get("현재가")),
            prev_close=parse_number(raw_data.get("전일")),
            open_price=parse_number(raw_data.get("시가")),
            high_price=parse_number(raw_data.get("고가")),
            low_price=parse_number(raw_data.get("저가")),
            volume=parse_int(raw_data.get("거래량")),
            trading_value=parse_number(raw_data.get("거래대금")),
            market_cap=parse_number(raw_data.get("시가총액")),
            shares_outstanding=parse_int(raw_data.get("상장주식수")),
            high_52week=parse_number(raw_data.get("52주최고")),
            low_52week=parse_number(raw_data.get("52주최저")),
            per=parse_number(raw_data.get("PER")),
            eps=parse_number(raw_data.get("EPS")),
            pbr=parse_number(raw_data.get("PBR(추정)")),
            dividend_yield=parse_number(raw_data.get("배당수익률")),
            raw_data=raw_data,
        )


@dataclass
class CompanyMetadata:
    """
    기업 메타데이터 모델
    
    Attributes:
        code: 종목 코드
        company_name: 기업명
        exchange: 거래소
        currency: 통화
        market_cap: 시가총액
        shares_outstanding: 발행 주식수
        latest_price: 최근 종가
        warnings: 경고 메시지 목록
    """
    code: str
    company_name: Optional[str] = None
    exchange: Optional[str] = None
    currency: str = "KRW"
    market_cap: Optional[float] = None
    shares_outstanding: Optional[int] = None
    latest_price: Optional[float] = None
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

    def add_warning(self, message: str) -> None:
        """경고 메시지 추가"""
        self.warnings.append(message)

    def calculate_shares_outstanding(self) -> None:
        """시가총액과 최근가로 발행주식수 계산"""
        if self.market_cap and self.latest_price and self.latest_price > 0:
            self.shares_outstanding = int(round(self.market_cap / self.latest_price))


@dataclass
class PriceHistory:
    """
    시세 이력 컨테이너 모델
    
    Attributes:
        code: 종목 코드
        start_date: 조회 시작일
        end_date: 조회 종료일
        prices: 일별 시세 목록
        fetched_at: 조회 시각
    """
    code: str
    start_date: str
    end_date: str
    prices: List[StockPrice] = field(default_factory=list)
    fetched_at: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "code": self.code,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "fetched_at": self.fetched_at,
            "count": len(self.prices),
            "prices": [p.to_dict() for p in self.prices],
        }

    def add_price(self, price: StockPrice) -> None:
        """시세 추가"""
        self.prices.append(price)

    @property
    def is_empty(self) -> bool:
        """데이터 존재 여부"""
        return len(self.prices) == 0

    @property
    def latest_price(self) -> Optional[StockPrice]:
        """가장 최근 시세"""
        if not self.prices:
            return None
        return max(self.prices, key=lambda p: p.date)

    @property
    def oldest_price(self) -> Optional[StockPrice]:
        """가장 오래된 시세"""
        if not self.prices:
            return None
        return min(self.prices, key=lambda p: p.date)


@dataclass 
class SiseRequest:
    """
    시세 조회 요청 파라미터 모델
    
    Attributes:
        code: 종목 코드
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        timeframe: 시간 단위
        order: 정렬 순서
        max_page: 최대 페이지 수 (HTML 크롤링용)
    """
    code: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    timeframe: TimeFrame = TimeFrame.DAY
    order: SortOrder = SortOrder.ASC
    max_page: int = 100

    def to_api_params(self) -> Dict[str, Any]:
        """API 호출용 파라미터로 변환"""
        return {
            "symbol": self.code,
            "requestType": 1,
            "startTime": self.start_date.replace("-", "") if self.start_date else None,
            "endTime": self.end_date.replace("-", "") if self.end_date else None,
            "timeframe": self.timeframe.value,
            "order": self.order.value,
            "output": "json",
        }

"""
Naver News Data Models

뉴스 데이터를 표현하는 데이터 클래스 모듈
"""

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