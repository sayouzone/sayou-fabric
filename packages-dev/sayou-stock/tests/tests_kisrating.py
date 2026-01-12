#!/usr/bin/env python3
"""
Kisrating Crawler 사용 예시
"""

import os
import pandas as pd
import sys

from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from kisrating import KisratingCrawler

def demo_statistics(crawler: KisratingCrawler, start_date: str = None):
    """한국신용평가 등급통계 조회 데모"""
    print(f"\n{'='*60}")
    print(f"한국신용평가 등급통계 조회")
    print('='*60)

    if start_date is None:
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        start_date = yesterday.strftime("%Y.%m.%d")

    # 한국신용평가 등급통계 조회
    print(f"\n한국신용평가 등급통계 조회 {start_date}")

    #data = crawler.statistics(start_date=start_date)
    data = crawler.statistics()
    print("\n수익률")
    print(data.yield_df)
    print("\n스프레드")
    print(data.spread_df)

    # 한국신용평가 등급통계 조회
    print(f"\n한국신용평가 등급통계 엑셀 다운로드 {start_date}")

    data = crawler.statistics_excel(start_date=start_date)
    print(data.filepath)

def main():
    """메인 데모 실행"""
    
    load_dotenv()

    # 한국신용평가에서 요구하는 User-Agent 설정
    crawler = KisratingCrawler()

    # 각 파일링 타입 데모
    demo_statistics(crawler)
    
    print("\n" + "="*60)
    print("Demo completed!")
    print("="*60)


if __name__ == "__main__":
    main()
