#!/usr/bin/env python3
"""
Koreainvestment RSI 사용 예시

기본 조건 (각 1점)

rsi_oversold: RSI < 30 (과매도 구간, 반등 가능성)
rsi_turning_up: RSI 상승 중 (모멘텀 전환)
volume_surge: 거래량 급증 (매집 신호)
golden_cross: 단기선 > 장기선 (상승 추세)

고급 조건 (상세 버전)

macd_golden: MACD 골든크로스
macd_hist_increasing: MACD 히스토그램 증가
bb_touch_lower: 볼린저 밴드 하단 (저가 매수)
above_ma60: 60일선 위 (장기 상승 추세)
rsi_divergence: RSI 다이버전스 (반전 신호)
"""

import os
import pandas as pd
import sys

from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from koreainvestment import KoreainvestmentCrawler

def demo_price(crawler: KoreainvestmentCrawler):
    """한국투자증권 주식 시세 조회 실행 예제"""
    print(f"\n{'='*60}")
    print(f"한국투자증권 주식 시세 조회 예제")
    print('='*60)

    # 국내주식 잔고 조회
    print(f"\nRSI 기반 투자 종목 분석 시작")

    # 분석할 종목 리스트 (예: KOSPI 대형주)
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

    for stock_code in stock_codes:
        data = crawler.price(stock_code)
        print(f"\n{stock_code} 시세")
        print(data)

    start_date = (datetime.now() - timedelta(days=200)).strftime("%Y%m%d")
    end_date = datetime.now().strftime("%Y%m%d")
    for stock_code in stock_codes:
        data = crawler.daily_price(stock_code, start_date, end_date)
        print(f"\n{stock_code} 일봉")
        print(data.response_body)
        print(data.info.to_korean())
        prices = []
        for price in data.prices:
            #print(price)
            prices.append({
                "date": datetime.strptime(price.stck_bsop_date, "%Y%m%d").strftime("%Y-%m-%d"),
                "open": int(price.stck_oprc),
                "high": int(price.stck_hgpr),
                "low": int(price.stck_lwpr),
                "close": int(price.stck_clpr),
                "volume": int(price.acml_vol),
            })
        
        df = pd.DataFrame(prices)
        print(df)

def demo_rsi(crawler: KoreainvestmentCrawler):
    """한국투자증권 RSI 기반 종목 선택 실행 예제"""
    print(f"\n{'='*60}")
    print(f"한국투자증권 RSI 기반 종목 선택 실행 예제")
    print('='*60)

    # Create the extracted filings folder if it doesn't exist
    rsi_folder = "./rsi"
    if not os.path.isdir(rsi_folder):
        os.mkdir(rsi_folder)

    # 국내주식 잔고 조회
    print(f"\nRSI 기반 투자 종목 분석 시작")

    # 분석할 종목 리스트 (예: KOSPI 대형주)
    stock_codes = [
        "005930", # 삼성전자
        "000660", # SK하이닉스
        "035420", # NAVER
        "005380", # 현대차
        "051910", # LG화학
        "006400", # 삼성SDI
        "035720", # 카카오
        "068270", # 셀트리온
        "207940", # 삼성바이오로직스
        "028260", # 삼성물산
        "105560", # KB금융지주
        "055550", # 신한금융지주회사
        "096770", # SK이노베이션
        "003670", # 포스코퓨처엠
        "017670", # SK텔레콤
    ]
    
    data = crawler.rsi(stock_codes=stock_codes, rsi_period=14, oversold_threshold=30, overbought_threshold=70)
    # 결과 출력
    print("\n" + "=" * 80)
    print("분석 결과")
    print("=" * 80)
    print(data.to_string(index=False))
    
    # 매수 추천 종목만 필터링
    buy_signals = data[data['signal'] == '매수']
    
    if not buy_signals.empty:
        print("\n" + "=" * 80)
        print(f"매수 추천 종목 ({len(buy_signals)}개)")
        print("=" * 80)
        print(buy_signals.to_string(index=False))
    else:
        print("\n현재 매수 추천 종목이 없습니다.")
    
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f'rsi_{timestamp}.csv'
    file_path = os.path.join(rsi_folder, filename)

    # CSV 저장
    data.to_csv(file_path, index=False, encoding='utf-8-sig')
    print(f"\n결과가 CSV 파일로 저장되었습니다.")

    result = {}

    # 3점 이상 종목만
    data = crawler.advanced_rsi(stock_codes=stock_codes)
    # 결과 출력
    print("\n" + "=" * 80)
    print("분석 결과")
    print("=" * 80)
    print(data.to_string(index=False))

    result['basic'] = data

    # 고득점 종목 필터링 (점수 3점 이상)
    high_score_stocks = data[data['score'] >= 3]
    
    if not high_score_stocks.empty:
        print("\n" + "=" * 100)
        print(f"추천 종목 (점수 3점 이상): {len(high_score_stocks)}개")
        print("=" * 100)
        print(high_score_stocks.to_string(index=False))
    
    # CSV 저장
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f'advanced_rsi_{timestamp}.csv'
    file_path = os.path.join(rsi_folder, filename)

    data.to_csv(file_path, index=False, encoding='utf-8-sig')
    print(f"\n결과 저장: {filename}")

    # 상세 분석 (파라미터 조정)
    print("\n" + "=" * 100)
    print("공격적 매수 조건 (RSI < 25, 거래량 2배)")
    print("=" * 100)
    
    data = crawler.advanced_rsi_detailed(
        stock_codes,
        rsi_threshold=25,        # 더 낮은 RSI
        volume_multiplier=2.0    # 더 많은 거래량
    )

    result['detailed'] = data
    
    # 강력추천/추천 종목만
    strong_buy = data[data['recommendation'].isin(['강력추천', '추천'])]
    print(f"\n강력추천/추천 종목: {len(strong_buy)}개")
    print(strong_buy[['stock_name', 'current_price', 'recommendation', 
                      'total_score', 'rsi', 'volume_ratio', 'bb_position']]
          .to_string(index=False))

    # 섹터별 분석
    print("\n" + "=" * 100)
    print("시나리오 3: 반도체 섹터 집중 분석")
    print("=" * 100)
    
    semiconductor_stocks = [
        "005930",  # 삼성전자
        "000660",  # SK하이닉스
        "042700",  # 한미반도체
        "039030",  # 이오테크닉스
        "058470",  # 리노공업
    ]

    data = crawler.advanced_rsi_detailed(semiconductor_stocks)

    result['sector'] = data
    
    print("\n반도체 섹터 분석 결과:")
    print(data[['stock_name', 'recommendation', 'total_score', 
                   'rsi', 'macd_hist', 'volume_ratio']].to_string(index=False))
    
    # ===== 결과 저장 및 리포트 =====
    
    # 엑셀 저장 (여러 시트)
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f'report_{timestamp}.xlsx'
    file_path = os.path.join(rsi_folder, filename)

    result1 = result['basic']
    result2 = result['detailed']
    result3 = result['sector']
    
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        result1.to_excel(writer, sheet_name='기본분석', index=False)
        result2.to_excel(writer, sheet_name='상세분석', index=False)
        result3.to_excel(writer, sheet_name='섹터분석', index=False)
    
    print(f"\n\n종합 리포트 저장: {filename}")

    # ===== 요약 통계 =====
    print("\n" + "=" * 100)
    print("분석 요약")
    print("=" * 100)
    print(f"총 분석 종목: {len(result1)}개")
    print(f"점수별 분포:")
    print(result1['score'].value_counts().sort_index(ascending=False))
    print(f"\n평균 RSI: {result1['rsi'].mean():.2f}")
    print(f"평균 거래량 비율: {result1['volume_ratio'].mean():.2f}배")

def main():
    """메인 데모 실행"""
    
    load_dotenv()

    app_key = os.getenv('KIS_APP_KEY')
    app_secret = os.getenv('KIS_APP_SECRET')

    # 한국신용평가에서 요구하는 User-Agent 설정
    crawler = KoreainvestmentCrawler(app_key, app_secret)

    # 각 파일링 타입 데모
    demo_price(crawler)
    #demo_rsi(crawler)
    
    print("\n" + "="*60)
    print("Demo completed!")
    print("="*60)


if __name__ == "__main__":
    main()
