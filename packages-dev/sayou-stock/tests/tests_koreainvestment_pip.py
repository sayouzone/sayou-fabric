#!/usr/bin/env python3
"""
Koreainvestment Crawler 사용 예시
"""

import os
from dotenv import load_dotenv

from sayou.stock.koreainvestment import KoreainvestmentCrawler

def demo_domestic(crawler: KoreainvestmentCrawler):
    """한국투자증권 국내 조회 데모"""
    print(f"\n{'='*60}")
    print(f"한국투자증권 국내 조회")
    print('='*60)

    # 국내주식 잔고 조회
    print(f"\n국내주식 잔고 조회")

    data = crawler.inquire_balance()
    print(data.response_body.to_korean())
    print(data.summary.to_korean())
    for balance in data.balances:
        print(balance.to_korean())

    print(f"\n상품기본조회[v1_국내주식-029]")
    data = crawler.search_info("005930")
    print(data.response_body.to_korean())
    print(data.info.to_korean())

    print(f"\n주식기본조회[v1_국내주식-067]")
    data = crawler.search_stock_info("005930")
    print(data.response_body.to_korean())
    print(data.info.to_korean())

def demo_domestic_finance(crawler: KoreainvestmentCrawler):
    """한국투자증권 국내 조회 데모"""
    print(f"\n{'='*60}")
    print(f"한국투자증권 국내 조회")
    print('='*60)

    print(f"\n국내주식 대차대조표[v1_국내주식-078]")
    data = crawler.balance_sheet("005930")
    print(data.response_body.to_korean())
    print(data.balance_sheet.to_korean())

    print(f"\n국내주식 손익계산서[v1_국내주식-079]")
    data = crawler.income_statement("005930")
    print(data.response_body.to_korean())
    for statement in data.statements:
        print(statement.to_korean())

    print(f"\n국내주식 재무비율[v1_국내주식-080]")
    data = crawler.financial_ratio("005930")
    print(data.response_body.to_korean())
    for ratio in data.ratios:
        print(ratio.to_korean())

    print(f"\n국내주식 수익성비율[v1_국내주식-081]")
    data = crawler.profit_ratio("005930")
    print(data.response_body.to_korean())
    for ratio in data.ratios:
        print(ratio.to_korean())

    print(f"\n국내주식 기타주요비율[v1_국내주식-082]")
    data = crawler.other_major_ratios("005930")
    print(data.response_body.to_korean())
    for ratio in data.ratios:
        print(ratio.to_korean())

    print(f"\n국내주식 안정성비율[v1_국내주식-083]")
    data = crawler.stability_ratio("005930")
    print(data.response_body.to_korean())
    for ratio in data.ratios:
        print(ratio.to_korean())

    print(f"\n국내주식 성장성비율[v1_국내주식-085]")
    data = crawler.growth_ratio("005930")
    print(data.response_body.to_korean())
    for ratio in data.ratios:
        print(ratio.to_korean())

def demo_domestic_ksdinfo(crawler: KoreainvestmentCrawler):
    """한국투자증권 국내 조회 데모"""
    print(f"\n{'='*60}")
    print(f"한국투자증권 국내 조회")
    print('='*60)

    print(f"\n예탁원정보(배당일정)[국내주식-145]")
    data = crawler.dividend("005930")
    print(data)
    for dividend in data.dividends:
        print(dividend.to_korean())

def demo_overseas(crawler: KoreainvestmentCrawler):
    """한국투자증권 해외 조회 데모"""
    print(f"\n{'='*60}")
    print(f"한국투자증권 해외 조회")
    print('='*60)

    # 해외주식 잔고 조회
    print(f"\n해외주식 잔고 조회")

    data = crawler.overseas_inquire_balance()
    print(data.response_body.to_korean())
    print(data.summary.to_korean())
    for balance in data.balances:
        print(balance.to_korean())

def main():
    """메인 데모 실행"""
    
    load_dotenv()

    app_key = os.getenv('KIS_APP_KEY')
    app_secret = os.getenv('KIS_APP_SECRET')

    # 한국신용평가에서 요구하는 User-Agent 설정
    crawler = KoreainvestmentCrawler(app_key, app_secret)

    # 각 파일링 타입 데모
    demo_domestic(crawler)
    demo_domestic_finance(crawler)
    demo_domestic_ksdinfo(crawler)
    demo_overseas(crawler)
    
    print("\n" + "="*60)
    print("Demo completed!")
    print("="*60)


if __name__ == "__main__":
    main()
