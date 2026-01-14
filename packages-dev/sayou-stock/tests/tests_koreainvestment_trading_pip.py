#!/usr/bin/env python3
"""
Koreainvestment Crawler 사용 예시
"""

import os
import pandas as pd
import sys

from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path

from sayou.stock.koreainvestment import KoreainvestmentCrawler

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
        print(balance.to_korean())
    df_balances = pd.DataFrame(balances)
    df_balances.drop(columns=["종합계좌번호", "계좌상품코드", "상품유형코드", "종목명", "대출유형코드"], inplace=True)
    print(df_balances)

def demo_overseas_trading(crawler: KoreainvestmentCrawler):
    """한국투자증권 해외 거래 데모"""
    print(f"\n{'='*60}")
    print(f"한국투자증권 해외 거래")
    print('='*60)

    buy_data = [
        ("DOW", 10, 24.0, "NYSE"),
        ("IONQ", 5, 40.0, "NYSE"), # 취소주문
        ("INUV", 100, 2.8, "AMEX")
    ]
    sell_data = [
        ("SPY", 2, 700.0, "AMEX"),
        #("KO", 10, 72.5, "NYSE"),  # 정상 주식을 매도
        ("KO", 10, 73.0, "NYSE"),  # 정상 주식을 정정주문
        ("QQQ", 1, 630.0, "NASD"),
        ("MVIS", 100, 1.2, "NASD"),
        ("IONQ", 5, 60.0, "NYSE"),
        ("INUV", 100, 4.0, "AMEX"),
        ("ARKG", 10, 35.0, "AMEX"),
        ("DOW", 10, 28.0, "NYSE"),
        ("NNDM", 100, 2.0, "NASD")
    ]

    order_no = {}
    # 해외주식 매수 주문
    print("\n해외주식 매수 주문")
    for info in buy_data:
        print(info)
        data = crawler.buy_stock_overseas(info[0], info[1], info[2], info[3])
        print(data.response_body.to_korean())
        print(data.order.to_korean())
        if info[0] == "IONQ":
            order_no["IONQ"] = data.order.ODNO
    
    # 해외주식 매도 주문
    print("\n해외주식 매도 주문")
    for info in sell_data:
        print(info)
        data = crawler.sell_stock_overseas(info[0], info[1], info[2], info[3])
        print(data.response_body.to_korean())
        print(data.order.to_korean())
        if info[0] == "KO":
            order_no["KO"] = data.order.ODNO

    revise_data = [
        ("KO", 10, 72.5, order_no.get("KO"), "NYSE")
    ]
    cancel_data = [
        ("IONQ", 5, 0, order_no.get("IONQ"), "NYSE")
    ]

    # 해외주식 정정주문
    print("\n해외주식 정정주문")
    for info in revise_data:
        print(info)
        data = crawler.revise_stock_overseas(info[0], info[1], info[2], info[3], info[4])
        print(data.response_body.to_korean())
        print(data.order.to_korean())
    
    # 해외주식 취소주문
    print("\n해외주식 취소주문")
    for info in cancel_data:
        print(info)
        data = crawler.cancel_stock_overseas(info[0], info[1], info[2], info[3], info[4])
        print(data.response_body.to_korean())
        print(data.order.to_korean())

def main():
    """메인 데모 실행"""
    
    load_dotenv()

    app_key = os.getenv('KIS_APP_KEY')
    app_secret = os.getenv('KIS_APP_SECRET')

    # 한국신용평가에서 요구하는 User-Agent 설정
    crawler = KoreainvestmentCrawler(app_key, app_secret)

    # 각 파일링 타입 데모
    demo_overseas(crawler)
    demo_overseas_trading(crawler)
    
    print("\n" + "="*60)
    print("Demo completed!")
    print("="*60)


if __name__ == "__main__":
    main()
