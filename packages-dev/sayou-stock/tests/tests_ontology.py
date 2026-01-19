#!/usr/bin/env python3
"""
Ontology 사용 예시
"""

import os
import pandas as pd
import sys

from dotenv import load_dotenv
from pathlib import Path

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from ontology import StockAnalyzer, StockKnowledgeGraph, KnowledgeGraphVisualizer
from koreainvestment import KoreainvestmentCrawler
from datetime import datetime, timedelta


def demo_ontology(analyzer: StockAnalyzer, crawler: KoreainvestmentCrawler):
    # 1. Knowledge Graph 초기화
    print("=" * 80)
    print("주식 Knowledge Graph 구축 시작")
    print("=" * 80)

    # 2. 종목 추가
    stocks_data = [
        {
            'code': '005930',
            'name': '삼성전자',
            'sector': '반도체',
            'industry': 'IT',
            'market': 'KOSPI',
            'marketCap': 400000000000000
        },
        {
            'code': '000660',
            'name': 'SK하이닉스',
            'sector': '반도체',
            'industry': 'IT',
            'market': 'KOSPI',
            'marketCap': 100000000000000
        },
        {
            'code': '035420',
            'name': 'NAVER',
            'sector': '인터넷',
            'industry': 'IT',
            'market': 'KOSPI',
            'marketCap': 50000000000000
        },
    ]

    """
    # 3. 주가 데이터 추가 (예시)
    sample_price_data = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=30, freq='D').strftime('%Y-%m-%d'),
        'open': range(70000, 100000, 1000),
        'high': range(71000, 101000, 1000),
        'low': range(69000, 99000, 1000),
        'close': range(70500, 100500, 1000),
        'volume': [1000000 + i * 10000 for i in range(30)]
    })
    print(sample_price_data)
    """
    
    start_date = (datetime.now() - timedelta(days=200)).strftime("%Y%m%d")
    end_date = datetime.now().strftime("%Y%m%d")

    for stock in stocks_data:
        stock_code = stock.pop('code')
        name = stock.pop('name')

        data = crawler.daily_price(stock_code, start_date, end_date)
        
        price_data = pd.DataFrame([{
            'date': datetime.strptime(item.stck_bsop_date, "%Y%m%d").strftime("%Y-%m-%d"),
            'open': int(item.stck_oprc),
            'high': int(item.stck_hgpr),
            'low': int(item.stck_lwpr),
            'close': int(item.stck_clpr),
            'volume': int(item.acml_vol)
        } for item in data.prices])

        analyzer.add_stock(stock_code, name, price_data,**stock)
    
    # 6. 종목 간 상관관계 추가
    analyzer.add_correlation("005930", "000660")
    print("상관관계 추가 완료")
    
    # 7. 쿼리 및 분석
    print("\n" + "=" * 80)
    print("분석 결과")
    print("=" * 80)
    
    # 상승 추세 종목
    uptrend_stocks = analyzer.query_stocks_by_trend('Uptrend')
    print(f"\n상승 추세 종목: {uptrend_stocks}")
    
    # 매수 신호 종목
    buy_signals = analyzer.query_stocks_with_buy_signal(min_confidence=0.6)
    print(f"\n매수 신호 종목:")
    for signal in buy_signals:
        print(f"  {signal['name']} ({signal['code']}): "
              f"신뢰도 {signal['confidence']:.2f}, 날짜 {signal['date']}")
    
    # 섹터 분석
    sector_df = analyzer.query_sector_analysis()
    print(f"\n섹터별 종목 수:")
    print(sector_df)
    
    # 종목 상세 정보
    summary = analyzer.get_stock_summary(stock_code)
    print(f"\n삼성전자 정보:")
    print(f"  섹터: {summary['sector']}")
    print(f"  산업: {summary['industry']}")
    print(f"  시장: {summary['market']}")
    
    # 8. 온톨로지 저장
    ontology_dir = "./ontology"
    if not os.path.exists(ontology_dir):
        os.makedirs(ontology_dir)

    filename = "stock_ontology.ttl"
    file_path = os.path.join(ontology_dir, filename)

    analyzer.save_ontology(file_path, format='turtle')
    
    # 9. 시각화
    print("\n" + "=" * 80)
    print("시각화 생성")
    print("=" * 80)
    
    visualizer = KnowledgeGraphVisualizer(analyzer)

    filename = "stock_knowledge_graph.html"
    file_path = os.path.join(ontology_dir, filename)
    visualizer.visualize_interactive(file_path)

    filename = "sector_distribution.png"
    file_path = os.path.join(ontology_dir, filename)
    visualizer.plot_sector_distribution(file_path)
    
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
    demo_ontology(analyzer, crawler)


if __name__ == "__main__":
    main()