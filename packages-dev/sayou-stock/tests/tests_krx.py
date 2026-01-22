#!/usr/bin/env python3
"""
Ontology 사용 예시
"""

import dart_fss as dart
import os
import pandas as pd
import sys

from datetime import datetime, timedelta
from dotenv import load_dotenv
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD
from pathlib import Path
from pykrx import stock

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from krx import KrxCrawler

# 네임스페이스 정의
FIBO = Namespace("https://spec.edmcouncil.org/fibo/ontology/")
DART = Namespace("https://opendart.fss.or.kr/ontology/")
KIFRS = Namespace("https://fss.or.kr/kifrs/")

def demo_dart():
    # 기업 검색 및 재무제표 추출
    corp_list = dart.get_corp_list()
    samsung = corp_list.find_by_corp_code('00126380')

    # XBRL 데이터 파싱
    reports = samsung.search_filings(bgn_de='20240101', pblntf_detail_ty='a001')
    xbrl = reports[0].xbrl
    #balance_sheet = xbrl.get_balance_sheets()
    balance_sheet = xbrl.get_financial_statement()
    #print(balance_sheet, type(balance_sheet))
    df = balance_sheet[0].to_DataFrame()
    print(df)

def dart_to_rdf(corp_code: str, year: str, tp: str, fs, g: Graph):
    items = {
        "bs": ("BalanceSheetItem", "재무상태표 컬럼"),
        "is": ("IncomeStatementItem", "손익계산서 컬럼"),
        "cf": ("CashFlowStatementItem", "현금흐름표 컬럼"),
        "cis": ("ConsolidatedIncomeStatementItem", "재무상태표(연결) 컬럼")
    }
    item, label = items.get(tp)
    df = fs.show(tp)
    print(df)
    
    print(f"{label}: {df.columns.tolist()}")

    company_uri = URIRef(f"https://dart.fss.or.kr/entity/{corp_code}")

    # 가장 최근 연도의 값 사용
    value_cols = [(col_name, col) for col_name, col in df.columns if col not in ['concept_id', 'account_nm', 'account_detail', 'label_ko', 'label_en', 'class0', 'class1', 'class2', 'class3', 'class4']]
    print(value_cols)
    concept_cols = [(col_name, col) for col_name, col in df.columns if col in ['concept_id', 'account_nm', 'account_detail']]
    print(concept_cols)
    

    for idx, row in df.iterrows():
        concept = row.get(concept_cols[0])

        if value_cols:
            latest_col = value_cols[0]  # 가장 최근 컬럼
            value = row.get(latest_col)
            print(concept, latest_col, value)
            
            if value and str(value) not in ['', 'nan', 'None']:
                # concept 이름 정제
                concept_clean = concept.replace(' ', '_').replace('/', '_')
                fact_uri = URIRef(f"https://dart.fss.or.kr/fact/{corp_code}/{year}/{tp}/{concept_clean}")
                
                g.add((fact_uri, RDF.type, KIFRS[item]))
                g.add((fact_uri, RDFS.label, Literal(str(concept), lang='ko')))
                g.add((fact_uri, DART.company, company_uri))
                g.add((fact_uri, DART.reportYear, Literal(year)))
                g.add((fact_uri, DART.conceptId, Literal(concept)))
                g.add((fact_uri, DART.quarter, Literal(latest_col[0])))
                
                # 숫자 값 변환
                try:
                    numeric_value = float(str(value).replace(',', ''))
                    g.add((fact_uri, DART.value, Literal(numeric_value, datatype=XSD.decimal)))
                except (ValueError, TypeError) as e:
                    g.add((fact_uri, DART.valueText, Literal(str(value))))
                    print(f"ValueError: {value} {e}")
    print(f"{label} 항목 {len(df)}개 처리 완료")

def demo_dart_to_rdf():
    corp_code = "00126380"
    year = "2025"

    g = Graph()
    g.bind("fibo", FIBO)
    g.bind("dart", DART)
    
    corp_list = dart.get_corp_list()
    company = corp_list.find_by_corp_code(corp_code)
    
    # 기업 엔터티 생성
    company_uri = URIRef(f"https://dart.fss.or.kr/entity/{corp_code}")
    g.add((company_uri, RDF.type, FIBO['BE/LegalEntities/Corporation']))
    g.add((company_uri, RDFS.label, Literal(company.corp_name, lang='ko')))
    g.add((company_uri, DART.corpCode, Literal(corp_code)))
    g.add((company_uri, DART.stockCode, Literal(company.stock_code)))

    # 재무제표 추출 (올바른 방법)
    # extract_fs()는 DataFrame을 반환
    # dart_fss.corp.corp.Corp
    # dart_fss.fs.fs.FinancialStatement
    try:
        fs = company.extract_fs(bgn_de=f'{year}0101', report_tp='quarter')
        #fs = company.extract_fs(bgn_de=f'{year}0101', report_tp='annual')

        if fs is None:
            print("재무제표를 찾을 수 없습니다.")
            return g
        
        # 재무상태표 (Balance Sheet)
        # bs: 재무상태표(balance sheet), is: 손익계산서(income statement), cf: 현금흐름표(cash flow statement), cis: 재무상태표(consolidated income statement)
        for tp in ['bs', 'is', 'cf', 'cis']:
            dart_to_rdf(corp_code, year, tp, fs, g)
                        
    except Exception as e:
        print(f"재무제표 추출 오류: {e}")
        import traceback
        traceback.print_exc()

    # RDF 저장
    base_dir = "./ontology"
    output_path = f"{base_dir}/{company.corp_name}[{company.stock_code},{corp_code}]_{year}_kg.ttl"
    g.serialize(output_path, format="turtle")
    print(f"\nKnowledge Graph 저장 완료: {output_path}")
    print(f"총 Triple 수: {len(g)}")

def demo_krx(crawler: KrxCrawler):
    data = crawler.krx_index(base_date="20260119")
    print(data)

def main():
    """Knowledge Graph 구축 및 분석 예제"""

    load_dotenv()

    auth_key = os.getenv("KRX_AUTH_KEY")
    print(auth_key)

    crawler = KrxCrawler(auth_key)
    
    # Knowledge Graph 구축 및 분석
    #demo_dart()
    #demo_dart_to_rdf()
    demo_krx(crawler)

if __name__ == "__main__":
    main()
