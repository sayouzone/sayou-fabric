#!/usr/bin/env python3
"""
FnGuide Crawler 사용 예시
"""

import os
import pandas as pd
import sys

from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from fnguide import FnGuideCrawler

def demo_main(crawler: FnGuideCrawler, code: str):
    """FnGuide 기업 정보 | Snapshot 조회 데모"""
    print(f"\n{'='*60}")
    print(f"FnGuide 기업 정보 | Snapshot을 조회 - {code}")
    print('='*60)

    #corp_code = crawler.fetch_corp_code("삼성전자")
    #print(corp_code)
    data = crawler.main(code)
    print(data)

    for key in data:
        list = data.get(key, [])
        if len(list) > 0:
            #print(f"\n{api_type} {last_year}년 ({corp_name}, {corp_code})")
            df = pd.DataFrame(list)
            #rcept_no = df.get("rcept_no")
            print(df)

def demo_finance(crawler: FnGuideCrawler, code: str):
    """FnGuide 기업 정보 | 재무제표 조회 데모"""
    print(f"\n{'='*60}")
    print(f"FnGuide 기업 정보 | 재무제표를 조회 - {code}")
    print('='*60)

    #corp_code = crawler.fetch_corp_code("삼성전자")
    #print(corp_code)
    data = crawler.finance(code)
    print(data)

    for key in data:
        list = data.get(key, [])
        if len(list) > 0:
            #print(f"\n{api_type} {last_year}년 ({corp_name}, {corp_code})")
            df = pd.DataFrame(list)
            #rcept_no = df.get("rcept_no")
            print(df)

def main(stock: str):
    """메인 데모 실행"""
    
    load_dotenv()

    #dart_api_key = os.getenv("DART_API_KEY", "")

    # FnGuide에서 요구하는 User-Agent 설정
    crawler = FnGuideCrawler()

    # 각 파일링 타입 데모
    demo_main(crawler, stock)
    demo_finance(crawler, stock)
    
    print("\n" + "="*60)
    print("Demo completed!")
    print("="*60)


if __name__ == "__main__":
    # 삼성전자, 하이닉스, 네이버 예시
    code = "005930" # 삼성전자
    main(code)
