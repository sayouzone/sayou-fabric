#!/usr/bin/env python3
"""
Ontology 사용 예시
"""

import dart_fss as dart
import os
import pandas as pd
import sys

from datetime import date, datetime, timedelta
from decimal import Decimal
from dotenv import load_dotenv
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD
from pathlib import Path
from pykrx import stock

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from yahoo import YahooCrawler
from koreainvestment import KoreainvestmentCrawler
from opendart import OpenDartCrawler

from fibo_kg import FiboKgCrawler
from fibo_kg.adapters import DartAdapter, NaverNewsAdapter, YahooAdapter, KoreainvestmentAdapter
from fibo_kg.processors import NewsProcessor
from fibo_kg.kg import KnowledgeGraphBuilder, SPARQLQueryHelper
from fibo_kg.models import (
    Company, DailyPrice, TechnicalIndicator,
    ReportingPeriod, BalanceSheet, IncomeStatement,
    CashFlowStatement, FinancialRatio,
    NewsSource, SentimentAnalysis, Topic, NewsArticle,
    MarketType, ReportType, SentimentLabel
)

def demo_news(naver_client_id: str, naver_client_secret: str):
    # 기업 검색 및 재무제표 추출
    crawler = FiboKgCrawler(naver_client_id=naver_client_id, naver_client_secret=naver_client_secret)
    naver_news_datasource = crawler.naver_news_datasource

    processor = NewsProcessor(naver_news_datasource)
    articles = processor.process_news("삼성전자", max_results=100)
    print(articles)
    
    #crawler.news("삼성전자", start_date="2026-01-01", max_results=100)
    #news_articles = crawler.news("삼성전자")
    #print(news_articles)

def demo_yahoo():
    crawler = YahooCrawler()
    adapter = YahooAdapter(crawler)

    prices = adapter.daily_prices("AAPL", datetime(2022, 1, 1), datetime(2022, 12, 31))
    print(prices)

    price = adapter.current_price("AAPL")
    print(price)

    news_articles = adapter.news("AAPL", max_results=100)
    print(news_articles)

def demo_dart():
    load_dotenv()

    base_dir = "./opendart"
    filename = "corpcode.json"
    filepath = os.path.join(base_dir, filename)

    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
    
    crawler = OpenDartCrawler(api_key=dart_api_key, corpcode_filename=filepath)
    crawler.save_corp_data(filepath)

    adapter = DartAdapter(crawler)

    stock_code = "005930"
    corp_name = "삼성전자"
    company = adapter.company_info(corp_name)
    print(company)

    bs, income, cf = adapter.financial_statements(company.corp_code, 2025)
    print(f"Balance Sheet: {bs}")
    print(f"Income Statement: {income}")
    print(f"Cash Flow Statement: {cf}")

    ratios = adapter.financial_ratios_from_statements(bs, income)
    print(f"Financial Ratios: {ratios}")

    disclosures = adapter.disclosures(company.corp_code, start_date = "2025-01-01", end_date = "2025-12-31")
    print(disclosures)

def demo_kg():
    load_dotenv()
    
    dart_api_key = os.getenv("DART_API_KEY")
    kis_app_key = os.getenv('KIS_APP_KEY')
    kis_app_secret = os.getenv('KIS_APP_SECRET')
    
    base_dir = "./opendart"
    filename = "corpcode.json"
    filepath = os.path.join(base_dir, filename)

    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
    
    crawler = OpenDartCrawler(api_key=dart_api_key, corpcode_filename=filepath)
    crawler.save_corp_data(filepath)

    adapter = DartAdapter(crawler)

    builder = KnowledgeGraphBuilder()

    stock_codes = ["005930", "000660"]
    #companies = []
    for stock_code in stock_codes:
        company = adapter.company_info(stock_code)
        #companies.append(company)
        builder.add_company(company)
    #print(companies)

    kis_crawler = KoreainvestmentCrawler(app_key=kis_app_key, app_secret=kis_app_secret)
    kis_adapter = KoreainvestmentAdapter(kis_crawler)

    today = date.today()
    yesterday = today - timedelta(days=1)
    one_year_ago = today - timedelta(days=365)

    # 주가 데이터
    #price = kis_adapter.current_price("005930")
    #print(price)
    for stock_code in stock_codes:
        data = kis_adapter.daily_prices(stock_code)
        for price in data:
            if price.trade_date > yesterday:
                continue
            print(price)
            builder.add_daily_price(price)

    """
    # 주가 데이터
    samsung_prices = [
        DailyPrice(
            stock_code="005930",
            trade_date=date(2024, 12, 20),
            open_price=Decimal("53000"),
            high_price=Decimal("53500"),
            low_price=Decimal("52500"),
            close_price=Decimal("53200"),
            volume=15000000,
            trading_value=Decimal("798000000000"),
            price_change=Decimal("200"),
            price_change_rate=Decimal("0.38"),
            market_cap=Decimal("317594000000000")
        ),
        DailyPrice(
            stock_code="005930",
            trade_date=date(2024, 12, 19),
            open_price=Decimal("53200"),
            high_price=Decimal("53800"),
            low_price=Decimal("52800"),
            close_price=Decimal("53000"),
            volume=18000000,
            trading_value=Decimal("954000000000"),
            price_change=Decimal("-200"),
            price_change_rate=Decimal("-0.38"),
            market_cap=Decimal("316400000000000")
        ),
    ]
    for price in samsung_prices:
        builder.add_daily_price(price)
    """
    
    # 재무제표 데이터
    period_2023 = ReportingPeriod(
        fiscal_year=2023,
        quarter=None,
        period_start=date(2023, 1, 1),
        period_end=date(2023, 12, 31),
        report_type=ReportType.ANNUAL
    )

    bs, income, cf = adapter.financial_statements(company.corp_code, 2025)
    """
    samsung_bs = BalanceSheet(
        corp_code="00126380",
        period=period_2023,
        total_assets=Decimal("455296000000000"),
        current_assets=Decimal("196896000000000"),
        non_current_assets=Decimal("258400000000000"),
        total_liabilities=Decimal("89046000000000"),
        current_liabilities=Decimal("55000000000000"),
        non_current_liabilities=Decimal("34046000000000"),
        total_equity=Decimal("366250000000000"),
        retained_earnings=Decimal("285000000000000")
    )
    print(samsung_bs)
    """
    print(bs)
    builder.add_balance_sheet(bs)
    
    """
    samsung_income = IncomeStatement(
        corp_code="00126380",
        period=period_2023,
        revenue=Decimal("258935000000000"),
        cost_of_sales=Decimal("185000000000000"),
        gross_profit=Decimal("73935000000000"),
        operating_income=Decimal("6567000000000"),
        net_income=Decimal("15487000000000"),
        eps=Decimal("2594")
    )
    print(samsung_income)
    """
    print(income)
    builder.add_income_statement(income)
    
    """
    samsung_cf = CashFlowStatement(
        corp_code="00126380",
        period=period_2023,
        operating_cash_flow=Decimal("68000000000000"),
        investing_cash_flow=Decimal("-55000000000000"),
        financing_cash_flow=Decimal("-12000000000000"),
        free_cash_flow=Decimal("13000000000000")
    )
    print(samsung_cf)
    """
    print(cf)
    builder.add_cash_flow_statement(cf)
    
    ratios = adapter.financial_ratios_from_statements(bs, income)
    samsung_ratio = FinancialRatio(
        corp_code="00126380",
        period=period_2023,
        per=Decimal("20.5"),
        pbr=Decimal("0.87"),
        roe=Decimal("4.23"),
        roa=Decimal("3.40"),
        debt_ratio=Decimal("24.32"),
        current_ratio=Decimal("357.99")
    )
    print(ratios)
    print(samsung_ratio)
    builder.add_financial_ratio(samsung_ratio)
    
    # 뉴스 데이터
    news_source = NewsSource(
        source_id="sample",
        source_name="샘플뉴스",
        source_url="https://example.com"
    )
    
    sentiment_positive = SentimentAnalysis(
        analysis_id="sent001",
        sentiment_score=Decimal("0.75"),
        sentiment_label=SentimentLabel.POSITIVE,
        confidence=Decimal("0.85"),
        analyzed_date=datetime(2024, 12, 20, 10, 30, 0)
    )
    
    topic_semiconductor = Topic(
        topic_id="topic001",
        topic_name="반도체",
        topic_name_en="Semiconductor"
    )
    
    news_article = NewsArticle(
        article_id="news001",
        title="삼성전자, 차세대 반도체 양산 시작",
        content="삼성전자가 차세대 반도체 양산을 본격적으로 시작했다. "
                "업계에서는 이번 양산이 실적 개선에 기여할 것으로 기대하고 있다.",
        published_date=datetime(2024, 12, 20, 9, 0, 0),
        url="https://example.com/news/001",
        author="홍길동 기자",
        source=news_source,
        sentiment=sentiment_positive,
        mentioned_companies=["005930"],
        topics=[topic_semiconductor]
    )
    builder.add_news_article(news_article)

    builder.serialize(format="turtle", destination="./ontology/kg.ttl")

    helper = SPARQLQueryHelper(builder.graph)
    
    print("\n" + "=" * 60)
    print("SPARQL 쿼리 예제")
    print("=" * 60)
    
    # 1. 모든 기업 조회
    print("\n1. 모든 상장기업 조회:")
    companies = helper.get_all_companies()
    for row in companies:
        print(f"   - {row.stockCode}: {row.corpName} ({row.market})")
    
    # 2. 특정 기업 정보 조회
    print("\n2. 삼성전자 정보 조회:")
    info = helper.get_company_by_code("005930")
    for row in info:
        print(f"   기업명: {row.corpName}")
        print(f"   영문명: {row.corpNameEn}")
        print(f"   산업: {row.industry}")
        print(f"   섹터: {row.sector}")
        print(f"   CEO: {row.ceo}")
    
    # 3. 재무비율 조회
    print("\n3. 삼성전자 재무비율:")
    ratios = helper.get_financial_ratios("005930")
    for row in ratios:
        print(f"   {row.year} PER: {row.per}, PBR: {row.pbr}, ROE: {row.roe}%")
    
    # 4. 뉴스 조회
    print("\n4. 삼성전자 관련 뉴스:")
    news = helper.get_news_by_company("005930")
    for row in news:
        print(f"   [{row.sentimentLabel}] {row.title}")
        print(f"   발행일: {row.publishedDate}")
    
    # 5. 커스텀 쿼리 예제
    print("\n5. 반도체 섹터 기업들:")
    sector_companies = helper.get_sector_comparison("반도체")
    for row in sector_companies:
        print(f"   - {row.stockCode}: {row.corpName}")


def main():
    """Knowledge Graph 구축 및 분석 예제"""

    load_dotenv()

    naver_client_id = os.getenv("NAVER_CLIENT_ID")
    naver_client_secret = os.getenv("NAVER_CLIENT_SECRET")

    auth_key = os.getenv("KRX_AUTH_KEY")
    #print(auth_key)

    dart_api_key = os.getenv("DART_API_KEY")

    kis_app_key = os.getenv('KIS_APP_KEY')
    kis_app_secret = os.getenv('KIS_APP_SECRET')
    
    # Knowledge Graph 구축 및 분석
    #demo_news(naver_client_id, naver_client_secret)
    #demo_yahoo()
    #demo_dart(dart_api_key)
    demo_kg()

if __name__ == "__main__":
    main()
