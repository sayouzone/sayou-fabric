#!/usr/bin/env python3
"""
Koreainvestment Crawler 사용 예시
"""

import argparse
import os
import pandas as pd
import sys

from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from koreainvestment import KoreainvestmentCrawler


def demo_overseas(crawler: KoreainvestmentCrawler):
    """한국투자증권 해외 조회 데모"""
    print(f"\n{'='*60}")
    print(f"한국투자증권 해외 조회")
    print('='*60)

    # 해외주식 잔고 조회
    print(f"\n해외주식 잔고 조회")

    data = crawler.inquire_balance_overseas()
    print(data.response_body.to_korean())
    print(data.summary.to_korean())
    balances = []
    for balance in data.balances:
        balances.append(balance.to_korean())
        #print(balance.to_korean())
    df_balances = pd.DataFrame(balances)
    df_balances.drop(columns=["종합계좌번호", "계좌상품코드", "상품유형코드", "종목명", "대출유형코드"], inplace=True)
    print(df_balances)

def demo_overseas_trading1(crawler: KoreainvestmentCrawler):
    """한국투자증권 해외 거래 데모"""
    print(f"\n{'='*60}")
    print(f"한국투자증권 해외 거래")
    print('='*60)

    buy_data = [
        #("DOW", 10, 24.0, "NYSE", "Buy"),
        ("DOW", 10, 26.0, "NYSE", "Buy"),
        ("INUV", 100, 2.8, "AMEX", "Buy")
    ]
    sell_data = [
        ("SPY", 2, 700.0, "AMEX", "Sell"),
        #("KO", 10, 72.5, "NYSE", "Sell"),  # 정상 주식을 매도
        ("KO", 10, 73.0, "NYSE", "Sell"),  # 정상 주식을 정정주문
        ("QQQ", 1, 630.0, "NASD", "Sell"),
        ("MVIS", 100, 1.2, "NASD", "Sell"),
        ("IONQ", 5, 60.0, "NYSE", "Sell"),
        ("INUV", 100, 4.0, "AMEX", "Sell"),
        ("ARKG", 10, 35.0, "AMEX", "Sell"),
        ("DOW", 10, 30.0, "NYSE", "Sell"),
        ("NNDM", 100, 2.0, "NASD", "Sell")
    ]

    orders = {}
    # 해외주식 매수 주문
    print("\n해외주식 매수 주문")
    for info in buy_data:
        print(info)
        ticker, quantity, price, market, order_type = info
        data = crawler.buy_stock_overseas(ticker, quantity, price, market)
        print(data.response_body.to_korean())
        if data.response_body.rt_cd != "0":
            continue

        print(data.order.to_korean())
        orders[ticker] = data.order.ODNO
    
    # 해외주식 매도 주문
    print("\n해외주식 매도 주문")
    for info in sell_data:
        print(info)
        ticker, quantity, price, market, order_type = info
        data = crawler.sell_stock_overseas(ticker, quantity, price, market)
        print(data.response_body.to_korean())
        if data.response_body.rt_cd != "0":
            continue

        print(data.order.to_korean())
        orders[ticker] = data.order.ODNO

    revise_data = [
        ("KO", 10, 72.5, orders.get("KO"), "NYSE", "Revise")
    ]
    cancel_data = [
    ]

    # 해외주식 정정주문
    print("\n해외주식 정정주문")
    for info in revise_data:
        print(info)
        ticker, quantity, price, order_no, market, order_type = info
        data = crawler.revise_stock_overseas(ticker, quantity, price, order_no, market)
        print(data.response_body.to_korean())
        if data.response_body.rt_cd != "0":
            continue
        print(data.order.to_korean())
    
    # 해외주식 취소주문
    print("\n해외주식 취소주문")
    for info in cancel_data:
        print(info)
        ticker, quantity, price, order_no, market, order_type = info
        data = crawler.cancel_stock_overseas(ticker, quantity, price, order_no, market)
        print(data.response_body.to_korean())
        if data.response_body.rt_cd != "0":
            continue
        print(data.order.to_korean())


def demo_overseas_trading(crawler: KoreainvestmentCrawler):
    """한국투자증권 해외거래 데모"""
    print(f"\n{'='*60}")
    print(f"한국투자증권 해외거래")
    print('='*60)

    trading_data = [
        #("DOW", 10, 24.0, "NYSE", "Buy"),
        ("DOW", 10, 26.0, "NYSE", "Buy"),
        ("INUV", 100, 2.8, "AMEX", "Buy"),
        ("SPY", 2, 700.0, "AMEX", "Sell"),
        #("KO", 10, 72.5, "NYSE", "Sell"),  # 정상 주식을 매도
        ("KO", 10, 73.0, "NYSE", "Sell"),  # 정상 주식을 정정주문
        ("QQQ", 1, 630.0, "NASD", "Sell"),
        ("MVIS", 100, 1.2, "NASD", "Sell"),
        ("IONQ", 5, 60.0, "NYSE", "Sell"),
        ("INUV", 100, 4.0, "AMEX", "Sell"),
        ("ARKG", 10, 35.0, "AMEX", "Sell"),
        ("DOW", 10, 30.0, "NYSE", "Sell"),
        ("NNDM", 100, 2.0, "NASD", "Sell"),
        ("KO", 10, 72.5, "NYSE", "Revise")
    ]

    # 해외주식 주문
    print("\n해외주식 주문")
    orders = {}
    for item in trading_data:
        print(item)
        ticker, quantity, price, market, order_type = item
        
        data = None
        if order_type == "Buy":
            data = crawler.buy_stock_overseas(ticker, quantity, price, market)
        elif order_type == "Sell":
            data = crawler.sell_stock_overseas(ticker, quantity, price, market)
        elif order_type == "Revise":
            order_no = orders.get(ticker)
            data = crawler.revise_stock_overseas(ticker, quantity, price, order_no, market)
        elif order_type == "Cancel":
            order_no = orders.get(ticker)
            data = crawler.cancel_stock_overseas(ticker, quantity, price, order_no, market)
        
        if data is None:
            continue

        print(data.response_body.to_korean())
        if data.response_body.rt_cd != "0":
            continue

        print(data.order.to_korean())
        orders[ticker] = data.order.ODNO


def demo_overseas_conclusion(crawler: KoreainvestmentCrawler):
    """한국투자증권 해외 거래 데모"""
    print(f"\n{'='*60}")
    print(f"한국투자증권 해외 거래")
    print('='*60)

    start_date = None
    if start_date is None:
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        start_date = yesterday.strftime("%Y%m%d")
        start_date1 = yesterday.strftime("%Y-%m-%d")

    # 해외주식 주문체결내역
    print(f"\n해외주식 주문체결내역 {start_date1}")
    data = crawler.conclusion_list_overseas("%", start_date, start_date, "%")
    conclusions = []
    for conclusion in data.conclusions:
        if conclusion.rvse_cncl_dvsn == "02":
            continue
        conclusions.append(conclusion.to_korean())
        #print(conclusion.to_korean())
    
    df_conclusions = pd.DataFrame(conclusions)
    columns = [
        "주문일자", "주문채번지점번호", "주문번호", "원주문번호", "매도매수구분코드", "정정취소구분", "정정취소구분명", "상품명",
        "처리상태명", "거부사유", "거부사유명", "주문시각", "거래시장명", "거래국가", "거래국가명", "거래통화코드", "국내주문일자", "당사주문시각", 
        "대출유형코드", "대출일자", "매체구분명", "미국애프터마켓연장신청여부", "분할매수/매도속성명"
    ]
    df_conclusions.drop(columns=columns, inplace=True)
    columns={
        '매도매수구분코드명': '구분', 
        '정정취소구분명': '정정구분', 
        'FT주문수량': '수량', 
        'FT주문단가3': '단가',
        'FT체결수량': '체결수량',
        'FT체결단가3': '체결단가',
        'FT체결금액3': '체결금액',
        '처리상태명': '처리상태',
        '거부사유명': '거부사유',
        '해외거래소코드': '거래소',
    }
    df_conclusions = df_conclusions.rename(columns=columns)
    print(df_conclusions)

def parse_args():
    parser = argparse.ArgumentParser(
        description='Command line to sell, buy, revise, cancel, & inquire overseas stocks')
    parser.add_argument('--type', help='Method type',
                        default='inquire')

    return parser.parse_args()

def main():
    """메인 데모 실행"""
    
    args = parse_args()
    
    load_dotenv()

    app_key = os.getenv('KIS_APP_KEY')
    app_secret = os.getenv('KIS_APP_SECRET')

    # 한국신용평가에서 요구하는 User-Agent 설정
    crawler = KoreainvestmentCrawler(app_key, app_secret)

    # 각 파일링 타입 데모
    if args.type == 'inquire':
        demo_overseas(crawler)
        demo_overseas_conclusion(crawler)
    elif args.type == 'trade':
        demo_overseas_trading(crawler)        
    elif args.type == 'trade1':
        demo_overseas_trading1(crawler)        
    
    print("\n" + "="*60)
    print("Demo completed!")
    print("="*60)


if __name__ == "__main__":
    main()
