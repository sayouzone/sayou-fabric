#!/usr/bin/env python3
"""
Ontology 사용 예시
"""

import os
import pandas as pd
import sys

from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from finance import StockAnalyzer, StockVisualizer
from finance import StockOntology, StockKnowledgeGraph
from finance import (
    CompanyData,
    FinancialData,
    StockPriceData,
    NewsData,
)

from koreainvestment import KoreainvestmentCrawler

def demo_kg(analyzer: StockAnalyzer, crawler: KoreainvestmentCrawler):
    stock_code = "005930"

    stock_codes = [
        "005930",  # 삼성전자
        "000660",  # SK하이닉스
        "035420",  # NAVER
        "005380",  # 현대차
        "051910",  # LG화학
        "006400",  # 삼성SDI
        "035720",  # 카카오
        "068270",  # 셀트리온
        "207940",  # 삼성바이오로직스
        "028260",  # 삼성물산
    ]
    stock_codes = [
        ("005930", "삼성전자", "반도체"),
        ("000660", "SK하이닉스", "반도체"),
        ("035420", "NAVER", "인터넷"),
        ("005380", "현대차", "자동차"),
        ("051910", "LG화학", "화학"),
        ("006400", "삼성SDI", "이차전지"),
        ("035720", "카카오", "인터넷"),
        ("068270", "셀트리온", "바이오"),
        ("207940", "삼성바이오로직스", "바이오"),
        ("028260", "삼성물산", "복합기업"),
        ("105560", "KB금융지주", "금융"),
        ("055550", "신한금융지주회사", "금융"),
        ("096770", "SK이노베이션", "석유화학"),
        ("003670", "포스코퓨처엠", "화학"),
        ("017670", "SK텔레콤", "통신"),
    ]

    for stock_code, name, sector in stock_codes:
        data = crawler.search_info(stock_code)
        company_name = data.info.prdt_abrv_name
        issue_date = data.info.frst_erlm_dt
        print(data)
    
        data = crawler.search_stock_info(stock_code)
        market = data.info.market # data.info.excg_dvsn_cd
        market_cap = int(data.info.cpta)
        industry = data.info.idx_bztp_mcls_cd_name  # 지수업종중분류코드명
        industry2 = data.info.std_idst_clsf_cd_name # 표준산업분류코드명
        print(data)
    
        industries = [industry, industry2]
        if sector not in industries:
            industries.append(sector)
        
        company_data = CompanyData(
            stock_code=stock_code,
            name=company_name,
            market=market,
            industry=industries,
            market_cap=market_cap,
            founded_date=issue_date
        )
        print(company_data)

        start_date = (datetime.now() - timedelta(days=200)).strftime("%Y%m%d")
        end_date = datetime.now().strftime("%Y%m%d")

        data = crawler.daily_price(stock_code, start_date, end_date)
        #print(data.info)
        eps = data.info.eps
        per = data.info.per
        pbr = data.info.pbr
        prices = data.prices

        data = crawler.balance_sheet(stock_code)
        balance_sheet = data.balance_sheets[0]
        #print(balance_sheet)
    
        data = crawler.income_statement(stock_code)
        income_statement = data.statements[0]
        #print(income_statement)
        net_income=float(income_statement.thtr_ntin) * 1_000_000
        operating_income=float(income_statement.bsop_prti) * 1_000_000
        revenue=float(income_statement.sale_account) * 1_000_000
        total_assets=float(balance_sheet.total_aset) * 1_000_000
        total_liabilities=float(balance_sheet.total_lblt) * 1_000_000
        total_equity=float(balance_sheet.total_cptl) * 1_000_000

        roe = round((net_income / total_equity) * 100, 2)

        # 재무 데이터 추가
        financials = FinancialData(
            stock_code=stock_code,
            period=balance_sheet.stac_yymm,
            revenue=revenue,                     # 매출액
            operating_income=operating_income,   # 영업이익
            net_income=net_income,               # 당기순이익
            total_assets=total_assets,           # 총자산
            total_liabilities=total_liabilities, # 총부채
            total_equity=total_equity,           # 총자본
            eps=float(eps),
            per=float(per),
            pbr=float(pbr),
            roe=roe
        )

        # 주가 데이터 추가
        price_data= [StockPriceData(
            stock_code=stock_code,
            date=price.stck_bsop_date,
            open_price=int(price.stck_oprc),
            high_price=int(price.stck_hgpr),
            low_price=int(price.stck_lwpr),
            close_price=int(price.stck_clpr),
            volume=int(price.acml_vol)
        ) for price in prices]

        analyzer.add_company(company_data, financials, price_data)

    # 뉴스 추가
    news = NewsData(
        news_id="news_001",
        title="삼성전자, AI 반도체 개발 가속화",
        content="삼성전자가 차세대 AI 반도체 개발에 박차를 가하고 있다...",
        published_date="2024-12-20T09:00:00",
        mentioned_companies=["005930"],
        sentiment=0.85
    )
    #analyzer.add_news(news)

    # 지식 그래프 저장
    analyzer.save_knowledge_graph()

def demo_rsi(analyzer: StockAnalyzer):
    # 상승 추세 종목
    # Uptrend, Downtrend, Sideways
    uptrend_stocks = analyzer.kg.query_stocks_by_trend('Uptrend')
    print(f"\n상승 추세 종목: {uptrend_stocks}")
    
    # 매수 신호 종목
    buy_signals = analyzer.kg.query_stocks_with_buy_signal(min_confidence=0.6)
    print(f"\n매수 신호 종목:")
    for signal in buy_signals:
        print(f"  {signal['name']} ({signal['code']}): "
              f"신뢰도 {signal['confidence']:.2f}, 날짜 {signal['date']}")
    
    # 섹터 분석
    sector_df = analyzer.kg.query_sector_analysis()
    print(f"\n섹터별 종목 수:")
    print(sector_df)
    
    # 종목 상세 정보
    summary = analyzer.kg.get_stock_summary('005930')
    print(f"\n삼성전자 정보:")
    print(f"  산업: {summary['industry']}")
    print(f"  시장: {summary['market']}")
    

def demo_analysis(analyzer: StockAnalyzer):
    stock_code = "005930"

    print("\n=== 기업 정보 조회 ===")
    company_info = analyzer.query_company_info(stock_code)
    print(company_info)
    
    print("\n=== 재무 지표 조회 ===")
    financials = analyzer.query_financial_metrics(stock_code, "202509")
    print(financials)
    
    print("\n=== 주가 정보 조회 ===")
    prices = analyzer.query_stock_prices(stock_code, "20250901", "20251231")
    #print(prices)
    for price in prices:
        print(price)


    # 산업 밸류에이션 비교
    print("=== 산업 밸류에이션 비교 ===")
    valuation_df = analyzer.analyze_valuation_comparison("반도체")
    print(valuation_df)

    # 저평가 종목 발굴
    print("\n=== 저평가 종목 ===")
    undervalued = analyzer.find_undervalued_stocks()
    print(undervalued)
    
    # 투자 리포트
    print("\n=== 투자 리포트 ===")
    report = analyzer.generate_investment_report(stock_code)
    print(report)
    
    base_dir = "./ontology"
    result_json_path = os.path.join(base_dir, "financial_kg_cytoscape.json")

    # 시각화
    visualizer = StockVisualizer(analyzer.kg)
    visualizer.export_to_cytoscape(result_json_path)

def demo_visualization(analyzer: StockAnalyzer):
    # 시각화
    print("\n" + "=" * 80)
    print("시각화 생성")
    print("=" * 80)
    
    visualizer = analyzer.visualizer

    filename = "stock_knowledge_graph.html"
    visualizer.visualize_interactive(filename)

    filename = "sector_distribution.png"
    visualizer.plot_sector_distribution(filename)
    
    # 10. SPARQL 쿼리 통계
    print(f"\n전체 트리플 수: {len(analyzer.graph)}")
    print(f"종목 수: {len(analyzer.stock_instances)}")
    
    print("\nKnowledge Graph 구축 완료!")

def main():
    """Knowledge Graph 구축 및 분석 예제"""

    load_dotenv()

    app_key = os.getenv('KIS_APP_KEY')
    app_secret = os.getenv('KIS_APP_SECRET')

    # Korea Investment Securities crawler 생성
    crawler = KoreainvestmentCrawler(app_key, app_secret)
    
    # Knowledge Graph 구축
    analyzer = StockAnalyzer()
    
    # Knowledge Graph 구축 및 분석
    #demo_kg(analyzer, crawler)
    demo_rsi(analyzer)
    demo_analysis(analyzer)
    demo_visualization(analyzer)


if __name__ == "__main__":
    main()