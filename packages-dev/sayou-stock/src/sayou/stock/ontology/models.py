from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CompanyData:
    """기업 데이터 클래스"""
    code: str
    name: str
    market: str
    industry: str
    market_cap: Optional[float] = None
    founded_date: Optional[str] = None


@dataclass
class FinancialData:
    """재무 데이터 클래스"""
    stock_code: str
    period: str  # YYYY-Q1 형식
    revenue: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    total_equity: Optional[float] = None
    eps: Optional[float] = None
    per: Optional[float] = None
    pbr: Optional[float] = None
    roe: Optional[float] = None


@dataclass
class StockPriceData:
    """주가 데이터 클래스"""
    stock_code: str
    date: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int


@dataclass
class NewsData:
    """뉴스 데이터 클래스"""
    news_id: str
    title: str
    content: str
    published_date: str
    mentioned_companies: List[str]
    sentiment: Optional[float] = None
