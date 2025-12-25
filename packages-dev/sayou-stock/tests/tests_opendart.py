#!/usr/bin/env python3
"""
OpenDart Crawler 사용 예시
"""

import os
import pandas as pd
import sys

from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from opendart import OpenDartCrawler

def demo_corp_code(crawler: OpenDartCrawler, code: str):
    """DART의 기업코드을 조회 데모"""
    print(f"\n{'='*60}")
    print(f"회사명 또는 종목코드로 DART의 기업코드을 조회 - {code}")
    print('='*60)

    #corp_code = crawler.fetch_corp_code("삼성전자")
    #print(corp_code)
    corp_code = crawler.fetch_corp_code(code)

    print(f"기업코드: {corp_code}")

def demo_base_documents(crawler: OpenDartCrawler, code: str):
    """기업의 기본 공시 문서 조회 데모"""
    print(f"\n{'='*60}")
    print(f"회사명 또는 종목코드로 DART의 기업코드을 조회 - {code}")
    print('='*60)

    corp_code = crawler.fetch_corp_code(code)
    data = crawler.company(corp_code) # 삼성전자, 005930, 00126380
    #ata = crawler.company(code) # 조회 안됨
    print(data, type(data))

    df = crawler.fetch(code)
    print(df)
    #print(df.to_string())
    #with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    #    print(df)

def demo_finance(crawler: OpenDartCrawler, corp_code: str):
    """정기보고서 재무정보 데모"""
    print(f"\n{'='*60}")
    print(f"정기보고서 재무정보 조회 - {code}")
    print('='*60)

    rcept_no = None

    # 지난해 (2024년) 정기보고서 재무정보 조회
    now = datetime.now()
    last_year = str(now.year - 1)

    corp_name = crawler.fetch_corp_name(corp_code)

    api_type = "단일회사 주요계정"
    data = crawler.finance(corp_code, last_year, api_type=api_type)
    #print(data)
    status = data.get("status", "")
    list = data.get("list", [])
    if status == "000" and len(list) > 0:
        print(f"\n{api_type} {last_year}년 ({corp_name}, {corp_code})")
        df = pd.DataFrame(list)
        rcept_no = df.get("rcept_no")
        print(df)

    api_type = "다중회사 주요계정"
    data = crawler.finance(corp_code, last_year, api_type=api_type)
    #print(data)
    status = data.get("status", "")
    list = data.get("list", [])
    if status == "000" and len(list) > 0:
        print(f"\n{api_type} {last_year}년 ({corp_name}, {corp_code})")
        df = pd.DataFrame(list)
        rcept_no = df.get("rcept_no")
        print(df)

    api_type = "단일회사 전체 재무제표"
    data = crawler.finance(corp_code, last_year, api_type=api_type)
    #print(data)
    status = data.get("status", "")
    list = data.get("list", [])
    if status == "000" and len(list) > 0:
        print(f"\n{api_type} {last_year}년 ({corp_name}, {corp_code})")
        df = pd.DataFrame(list)
        rcept_no = df.get("rcept_no")
        print(df)

    #api_type = "XBRL택사노미재무제표양식"
    api_type = "단일회사 주요 재무지표"
    data = crawler.finance(corp_code, last_year, api_type=api_type)
    #print(data)
    status = data.get("status", "")
    list = data.get("list", [])
    if status == "000" and len(list) > 0:
        print(f"\n{api_type} {last_year}년 ({corp_name}, {corp_code})")
        df = pd.DataFrame(list)
        print(df)

    api_type = "다중회사 주요 재무지표"
    data = crawler.finance(corp_code, last_year, api_type=api_type)
    #print(data)
    status = data.get("status", "")
    list = data.get("list", [])
    if status == "000" and len(list) > 0:
        print(f"\n{api_type} {last_year}년 ({corp_name}, {corp_code})")
        df = pd.DataFrame(list)
        print(df)

    # 올해 (2025년) 정기보고서 재무정보 조회
    current_year = str(now.year)
    quarter = (now.month - 1) // 3

    api_type = "단일회사 주요계정"
    data = crawler.finance(corp_code, current_year, quarter=quarter, api_type=api_type)
    #print(data)
    status = data.get("status", "")
    list = data.get("list", [])
    if status == "000" and len(list) > 0:
        print(f"\n{api_type} {current_year}년 {quarter}분기 ({corp_name}, {corp_code})")
        df = pd.DataFrame(list)
        rcept_no = df.get("rcept_no")
        print(df)

    api_type = "다중회사 주요계정"
    data = crawler.finance(corp_code, current_year, quarter=quarter, api_type=api_type)
    #print(data)
    status = data.get("status", "")
    list = data.get("list", [])
    if status == "000" and len(list) > 0:
        print(f"\n{api_type} {current_year}년 {quarter}분기 ({corp_name}, {corp_code})")
        df = pd.DataFrame(list)
        rcept_no = df.get("rcept_no")
        print(df)

    api_type = "단일회사 전체 재무제표"
    data = crawler.finance(corp_code, current_year, quarter=quarter, api_type=api_type)
    #print(data)
    status = data.get("status", "")
    list = data.get("list", [])
    if status == "000" and len(list) > 0:
        print(f"\n{api_type} {current_year}년 {quarter}분기 ({corp_name}, {corp_code})")
        df = pd.DataFrame(list)
        rcept_no = df.get("rcept_no")
        print(df)
    
    # 수익성지표 : M210000 안정성지표 : M220000 성장성지표 : M230000 활동성지표 : M240000
    indicator_code = "M210000"

    #api_type = "XBRL택사노미재무제표양식"
    api_type = "단일회사 주요 재무지표"
    data = crawler.finance(corp_code, current_year, quarter=quarter, api_type=api_type)
    #print(data)
    status = data.get("status", "")
    list = data.get("list", [])
    if status == "000" and len(list) > 0:
        idx_cl_nm = list[0].get("idx_cl_nm")
        print(f"\n{api_type} {current_year}년 {quarter}분기 {idx_cl_nm} ({corp_name}, {corp_code})")
        df = pd.DataFrame(list)
        print(df)

    api_type = "다중회사 주요 재무지표"
    data = crawler.finance(corp_code, current_year, quarter=quarter, api_type=api_type)
    #print(data)
    status = data.get("status", "")
    list = data.get("list", [])
    if status == "000" and len(list) > 0:
        idx_cl_nm = list[0].get("idx_cl_nm")
        print(f"\n{api_type} {current_year}년 {quarter}분기 {idx_cl_nm} ({corp_name}, {corp_code})")
        df = pd.DataFrame(list)
        print(df)

    indicator_code = "M220000"

    #api_type = "XBRL택사노미재무제표양식"
    api_type = "단일회사 주요 재무지표"
    data = crawler.finance(corp_code, current_year, quarter=quarter, api_type=api_type, indicator_code=indicator_code)
    #print(data)
    status = data.get("status", "")
    list = data.get("list", [])
    if status == "000" and len(list) > 0:
        idx_cl_nm = list[0].get("idx_cl_nm")
        print(f"\n{api_type} {current_year}년 {quarter}분기 {idx_cl_nm} ({corp_name}, {corp_code})")
        df = pd.DataFrame(list)
        print(df)

    api_type = "다중회사 주요 재무지표"
    data = crawler.finance(corp_code, current_year, quarter=quarter, api_type=api_type, indicator_code=indicator_code)
    #print(data)
    status = data.get("status", "")
    list = data.get("list", [])
    if status == "000" and len(list) > 0:
        idx_cl_nm = list[0].get("idx_cl_nm")
        print(f"\n{api_type} {current_year}년 {quarter}분기 {idx_cl_nm} ({corp_name}, {corp_code})")
        df = pd.DataFrame(list)
        print(df)

    indicator_code = "M230000"

    #api_type = "XBRL택사노미재무제표양식"
    api_type = "단일회사 주요 재무지표"
    data = crawler.finance(corp_code, current_year, quarter=quarter, api_type=api_type, indicator_code=indicator_code)
    #print(data)
    status = data.get("status", "")
    list = data.get("list", [])
    if status == "000" and len(list) > 0:
        idx_cl_nm = list[0].get("idx_cl_nm")
        print(f"\n{api_type} {current_year}년 {quarter}분기 {idx_cl_nm} ({corp_name}, {corp_code})")
        df = pd.DataFrame(list)
        print(df)

    api_type = "다중회사 주요 재무지표"
    data = crawler.finance(corp_code, current_year, quarter=quarter, api_type=api_type, indicator_code=indicator_code)
    #print(data)
    status = data.get("status", "")
    list = data.get("list", [])
    if status == "000" and len(list) > 0:
        idx_cl_nm = list[0].get("idx_cl_nm")
        print(f"\n{api_type} {current_year}년 {quarter}분기 {idx_cl_nm} ({corp_name}, {corp_code})")
        df = pd.DataFrame(list)
        print(df)

    indicator_code = "M240000"

    #api_type = "XBRL택사노미재무제표양식"
    api_type = "단일회사 주요 재무지표"
    data = crawler.finance(corp_code, current_year, quarter=quarter, api_type=api_type, indicator_code=indicator_code)
    #print(data)
    status = data.get("status", "")
    list = data.get("list", [])
    if status == "000" and len(list) > 0:
        idx_cl_nm = list[0].get("idx_cl_nm")
        print(f"\n{api_type} {current_year}년 {quarter}분기 {idx_cl_nm} ({corp_name}, {corp_code})")
        df = pd.DataFrame(list)
        print(df)

    api_type = "다중회사 주요 재무지표"
    data = crawler.finance(corp_code, current_year, quarter=quarter, api_type=api_type, indicator_code=indicator_code)
    #print(data)
    status = data.get("status", "")
    list = data.get("list", [])
    if status == "000" and len(list) > 0:
        idx_cl_nm = list[0].get("idx_cl_nm")
        print(f"\n{api_type} {current_year}년 {quarter}분기 {idx_cl_nm} ({corp_name}, {corp_code})")
        df = pd.DataFrame(list)
        print(df)

    # 올해 마지막 재무제표 접수번호
    print(f"\n{current_year}년 {quarter}분기 접수번호: {rcept_no.iloc[0]}")
    
    return rcept_no.iloc[0]

def demo_download_xbrl(crawler: OpenDartCrawler, rcept_no: str = None):
    """OpenDart 정기보고서 재무정보 - 재무제표 원본파일(XBRL). 다운로드"""
    print(f"\n{'='*60}")
    print(f"OpenDart 정기보고서 재무정보 - 재무제표 원본파일(XBRL) 다운로드 - {rcept_no}")
    print('='*60)

    #rcept_no = "20190401004781"
    rcept_no = "20250814003156" if not rcept_no else rcept_no
    save_path = crawler.finance_file(rcept_no, quarter = 4)
    
    if not save_path:
        print(f"파일이 존재하지 않습니다. {rcept_no}")
    else:
        print(f"저장 경로: {save_path}")

def demo_reports(crawler: OpenDartCrawler, corp_code: str):
    """정기보고서 주요정보 데모"""
    print(f"\n{'='*60}")
    print(f"회사명 또는 종목코드로 DART의 기업코드을 조회 - {code}")
    print('='*60)
    corp_name = crawler.fetch_corp_name(corp_code)

    rcept_no = None

    # 증자(감자) 현황
    year = "2024"
    quarter = 4
    api_no = 0

    api_key, data = crawler.reports(corp_code, year=year, quarter=quarter, api_no=api_no)
    #print(data)
    status = data.get("status", "")
    list = data.get("list", [])
    if status == "000" and len(list) > 0:
        #idx_cl_nm = list[0].get("idx_cl_nm")
        print(f"\n{api_key} {year}년 {quarter}분기 ({corp_name}, {corp_code})")
        df = pd.DataFrame(list)
        rcept_no = df.get("rcept_no")
        print(df)

        # 재무제표 접수번호
        print(f"\n{year}년 {quarter}분기 접수번호: {rcept_no.iloc[0]}")

    # 배당에 관한 사항
    year = "2025"
    quarter = 3
    api_no = 1

    api_key, data = crawler.reports(corp_code, year=year, quarter=quarter, api_no=api_no)
    #print(data)
    status = data.get("status", "")
    list = data.get("list", [])
    if status == "000" and len(list) > 0:
        #idx_cl_nm = list[0].get("idx_cl_nm")
        print(f"\n{api_key} {year}년 {quarter}분기 ({corp_name}, {corp_code})")
        df = pd.DataFrame(list)
        rcept_no = df.get("rcept_no")
        print(df)

        # 재무제표 접수번호
        print(f"\n{year}년 {quarter}분기 접수번호: {rcept_no.iloc[0]}")

def demo_ownership(crawler: OpenDartCrawler, corp_code: str):
    """지분공시 종합정보 데모"""
    print(f"\n{'='*60}")
    print(f"지분공시 종합정보를 조회 - {code}")
    print('='*60)
    corp_name = crawler.fetch_corp_name(corp_code)

    rcept_no = None

    # 대량보유 상황보고 현황
    api_no = 0

    api_key, data = crawler.ownership(corp_code, api_no=api_no)
    #print(data)
    status = data.get("status", "")
    list = data.get("list", [])
    if status == "000" and len(list) > 0:
        #idx_cl_nm = list[0].get("idx_cl_nm")
        print(f"\n{api_key} ({corp_name}, {corp_code})")
        df = pd.DataFrame(list)
        rcept_no = df.get("rcept_no")
        print(df)

        # 재무제표 접수번호
        print(f"\n접수번호: {rcept_no.iloc[0]}")

    # 임원ㆍ주요주주 소유보고 현황
    api_no = 1

    api_key, data = crawler.ownership(corp_code, api_no=api_no)
    #print(data)
    status = data.get("status", "")
    list = data.get("list", [])
    if status == "000" and len(list) > 0:
        #idx_cl_nm = list[0].get("idx_cl_nm")
        print(f"\n{api_key} ({corp_name}, {corp_code})")
        df = pd.DataFrame(list)
        rcept_no = df.get("rcept_no")
        print(df)

        # 재무제표 접수번호
        print(f"\n접수번호: {rcept_no.iloc[0]}")

def demo_material_facts(crawler: OpenDartCrawler, corp_code: str):
    """주요사항보고서 주요정보 데모"""
    print(f"\n{'='*60}")
    print(f"회사명 또는 종목코드로 DART의 주요사항보고서 주요정보를 조회 - {code}")
    print('='*60)
    corp_name = crawler.fetch_corp_name(corp_code)

    rcept_no = None

    # 자산양수도(기타), 풋백옵션 현황
    corp_code = "00409681"
    corp_name = crawler.fetch_corp_name(corp_code)
    start_date = "20190101"
    end_date = "20251231"
    api_no = 0

    api_key, data = crawler.material_facts(corp_code, start_date=start_date, end_date=end_date, api_no=api_no)
    #print(data)
    status = data.get("status", "")
    list = data.get("list", [])
    if status == "000" and len(list) > 0:
        #idx_cl_nm = list[0].get("idx_cl_nm")
        print(f"\n{api_key} ({corp_name}, {corp_code})")
        df = pd.DataFrame(list)
        rcept_no = df.get("rcept_no")
        print(df)

        # 재무제표 접수번호
        print(f"\n접수번호: {rcept_no.iloc[0]}")

    # 유무상증자 결정 현황
    corp_code = "00359395"
    corp_name = crawler.fetch_corp_name(corp_code)
    start_date = "20190101"
    end_date = "20251231"
    api_no = 7

    api_key, data = crawler.material_facts(corp_code, start_date=start_date, end_date=end_date, api_no=api_no)
    #print(data)
    status = data.get("status", "")
    list = data.get("list", [])
    if status == "000" and len(list) > 0:
        #idx_cl_nm = list[0].get("idx_cl_nm")
        print(f"\n{api_key} ({corp_name}, {corp_code})")
        df = pd.DataFrame(list)
        rcept_no = df.get("rcept_no")
        print(df)

        # 재무제표 접수번호
        print(f"\n접수번호: {rcept_no.iloc[0]}")

def demo_registration(crawler: OpenDartCrawler, corp_code: str):
    """증권신고서 주요정보 데모"""

    print(f"\n{'='*60}")
    print(f"회사명 또는 종목코드로 DART의 증권신고서 주요정보를 조회 - {code}")
    print('='*60)
    #corp_name = crawler.fetch_corp_name(corp_code)
    #start_date = "20150101"
    #end_date = "20251231"

    rcept_no = None

    # 증자(감자) 현황
    corp_code = "00106395"
    corp_name = crawler.fetch_corp_name(corp_code)
    start_date = "20190101"
    end_date = "20251231"

    api_no = 0

    api_key, data = crawler.registration(corp_code, start_date=start_date, end_date=end_date, api_no=api_no)
    #print(data)
    status = data.get("status", "")
    groups = data.get("group", [])
    if status == "000" and len(groups) > 0:
        for item in groups:
            title = item.get("title")
            list = item.get("list")
            print(f"\n{api_key} {title} ({corp_name}, {corp_code})")
            df = pd.DataFrame(list)
            rcept_no = df.get("rcept_no")
            print(df)

            # 재무제표 접수번호
            print(f"\n접수번호: {rcept_no.iloc[0]}")

    # 채무증권 현황
    corp_code = "00858364"
    corp_name = crawler.fetch_corp_name(corp_code)
    start_date = "20190101"
    end_date = "20251231"

    api_no = 1

    api_key, data = crawler.registration(corp_code, start_date=start_date, end_date=end_date, api_no=api_no)
    #print(data)
    status = data.get("status", "")
    groups = data.get("group", [])
    if status == "000" and len(groups) > 0:
        for item in groups:
            title = item.get("title")
            list = item.get("list")
            print(f"\n{api_key} {title} ({corp_name}, {corp_code})")
            df = pd.DataFrame(list)
            rcept_no = df.get("rcept_no")
            print(df)

            # 재무제표 접수번호
            print(f"\n접수번호: {rcept_no.iloc[0]}")

    # 증권예탁증권 현황
    corp_code = "01338724"
    corp_name = crawler.fetch_corp_name(corp_code)
    start_date = "20190101"
    end_date = "20251231"

    api_no = 2

    api_key, data = crawler.registration(corp_code, start_date=start_date, end_date=end_date, api_no=api_no)
    #print(data)
    status = data.get("status", "")
    groups = data.get("group", [])
    if status == "000" and len(groups) > 0:
        for item in groups:
            title = item.get("title")
            list = item.get("list")
            print(f"\n{api_key} {title} ({corp_name}, {corp_code})")
            df = pd.DataFrame(list)
            rcept_no = df.get("rcept_no")
            print(df)

            # 재무제표 접수번호
            #print(f"\n접수번호: {rcept_no.iloc[0]}")

    # 합병 현황    
    corp_code = "00109718"
    #corp_code = crawler.fetch_corp_code(corp_code)
    corp_name = crawler.fetch_corp_name(corp_code)
    print(corp_code, corp_name)
    start_date = "20190101"
    end_date = "20251231"

    api_no = 3
    print(f"\nOpenDart 합병 현황 ({corp_name}, {corp_code})")

    #api_key, data = crawler.registration(corp_code, start_date=start_date, end_date=end_date, api_no=api_no)
    api_key, data = crawler.merge(corp_code, start_date=start_date, end_date=end_date)
    #print(data)
    status = data.get("status", "")
    groups = data.get("group", [])
    if status == "000" and len(groups) > 0:
        for item in groups:
            title = item.get("title")
            list = item.get("list")
            print(f"\n{api_key} {title} ({corp_name}, {corp_code})")
            df = pd.DataFrame(list)
            rcept_no = df.get("rcept_no")
            print(df)

            # 재무제표 접수번호
            #print(f"\n접수번호: {rcept_no.iloc[0]}")

    # 분할 현황    
    corp_code = "00105271"
    #corp_code = crawler.fetch_corp_code(corp_code)
    corp_name = crawler.fetch_corp_name(corp_code)
    print(corp_code, corp_name)
    start_date = "20190101"
    end_date = "20251231"

    api_no = 5
    print(f"\nOpenDart 분할 현황 ({corp_name}, {corp_code})")

    #api_key, data = crawler.registration(corp_code, start_date=start_date, end_date=end_date, api_no=api_no)
    api_key, data = crawler.split(corp_code, start_date=start_date, end_date=end_date)
    #print(data)
    status = data.get("status", "")
    groups = data.get("group", [])
    if status == "000" and len(groups) > 0:
        for item in groups:
            title = item.get("title")
            list = item.get("list")
            print(f"\n{api_key} {title} ({corp_name}, {corp_code})")
            df = pd.DataFrame(list)
            rcept_no = df.get("rcept_no")
            print(df)

            # 재무제표 접수번호
            #print(f"\n접수번호: {rcept_no.iloc[0]}")

def main(code: str):
    """메인 데모 실행"""
    
    load_dotenv()
    dart_api_key = os.getenv("DART_API_KEY", "")

    # OpenDart에서 요구하는 User-Agent 설정
    crawler = OpenDartCrawler(api_key=dart_api_key)

    # 회사이름으로 corp_code 검색
    #company_name = "삼성전자"
    #corp_code = crawler.fetch_corp_code(company_name)
    corp_code = crawler.fetch_corp_code(code)
    if not corp_code:
        print(f"Could not find corp_code for {code}")
        return

    print(f"\n{code} corp_code: {corp_code}")

    # 각 파일링 타입 데모
    #demo_corp_code(crawler, code)
    #demo_base_documents(crawler, code)
    #rcept_no = demo_finance(crawler, corp_code)
    # 00126380      삼성전자     005930        Y                  반기보고서 (2025.06)  20250814003156              삼성전자  20250814  
    #rcept_no="20251114002447"
    #demo_download_xbrl(crawler, rcept_no=rcept_no)
    #demo_reports(crawler, corp_code)
    #demo_ownership(crawler, corp_code)
    #demo_material_facts(crawler, corp_code)
    #demo_registration(crawler, corp_code)
    crawler.duplicate_keys()
    
    print("\n" + "="*60)
    print("Demo completed!")
    print("="*60)


if __name__ == "__main__":
    # 삼성전자, 하이닉스, 네이버 예시
    code = "005930" # 삼성전자
    main(code)
