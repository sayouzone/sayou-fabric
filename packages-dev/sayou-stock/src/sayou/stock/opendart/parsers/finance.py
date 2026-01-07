# Copyright (c) 2025, Sayouzone
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
 
import io
import zipfile
import re
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from urllib.parse import unquote

from ..client import OpenDartClient
from ..models import (
    IndexClassCode,
    FinanceStatus,
    OpenDartRequest,
    SingleCompanyMainAccountsData,
    MultiCompanyMainAccountsData,
    XBRLTaxonomyFinancialStatementData,
    SingleFinancialStatementData,
    SingleCompanyKeyFinancialIndicatorData,
    MultiCompanyKeyFinancialIndicatorData,
)
from ..utils import (
    decode_euc_kr,
    quarters,
    FINANCE_COLUMNS,
    save_zip_path,
    parse_xml,
    parse_unzip_xml,
    save_zip,
    save_unzip,
)

class OpenDartFinanceParser:
    """
    OpenDART 정기보고서 재무정보 API 파싱 클래스
    
    정기보고서 재무정보: Financial Information in Periodic Reports, https://opendart.fss.or.kr/guide/main.do?apiGrpCd=DS003
    """

    # 재무제표구분
    # https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS003&apiId=2020001
    FINANCIAL_STATEMENTS_TYPES = {
        "BS1": ("재무상태표", "연결", "유동/비유동법", None),                # BS (Balance Sheet) : 재무상태표
        "BS2": ("재무상태표", "개별", "유동/비유동법", None),
        "BS3": ("재무상태표", "연결", "유동성배열법", None),
        "BS4": ("재무상태표", "개별", "유동성배열법", None),
        "IS1": ("별개의 손익계산서", "연결", "기능별분류", None),              # IS (Income Statement) : 손익계산서
        "IS2": ("별개의 손익계산서", "개별", "기능별분류", None),
        "IS3": ("별개의 손익계산서", "연결", "성격별분류", None),
        "IS4": ("별개의 손익계산서", "개별", "성격별분류", None),
        "CIS1": ("포괄손익계산서", "연결", "세후", None),                    # CIS (Consolidated Income Statement) : 포괄손익계산서
        "CIS2": ("포괄손익계산서", "개별", "세후", None),
        "CIS3": ("포괄손익계산서", "연결", "세전", None),
        "CIS4": ("포괄손익계산서", "개별", "세전", None),
        "DCIS1": ("단일 포괄손익계산서", "연결", "기능별분류", "세후포괄손익"),    # DCIS (Detailed Consolidated Income Statement) : 단일 포괄손익계산서
        "DCIS2": ("단일 포괄손익계산서", "개별", "기능별분류", "세후포괄손익"),
        "DCIS3": ("단일 포괄손익계산서", "연결", "기능별분류", "세전"),
        "DCIS4": ("단일 포괄손익계산서", "개별", "기능별분류", "세전"),
        "DCIS5": ("단일 포괄손익계산서", "연결", "성격별분류", "세후포괄손익"),
        "DCIS6": ("단일 포괄손익계산서", "개별", "성격별분류", "세후포괄손익"),
        "DCIS7": ("단일 포괄손익계산서", "연결", "성격별분류", "세전"),
        "DCIS8": ("단일 포괄손익계산서", "개별", "성격별분류", "세전"),
        "CF1": ("현금흐름표", "연결", "직접법", None),                      # CF (Cash Flow) : 현금흐름표
        "CF2": ("현금흐름표", "개별", "직접법", None), 
        "CF3": ("현금흐름표", "연결", "간접법", None),
        "CF4": ("현금흐름표", "개별", "간접법", None),
        "SCE1": ("자본변동표", "연결", None, None),                        # SCE (Statement of Changes in Equity) : 자본변동표
        "SCE2": ("자본변동표", "개별", None, None),
    }

    def __init__(self, client: OpenDartClient):
        self.client = client

        self._balance_sheet = None
        self._income_statement = None
        self._consolidated_income_statement = None
        self._cash_flow_statement = None
        self._equity_statement = None

        self._df_cis = pd.DataFrame()
        self._df_is = pd.DataFrame()
        self._df_bs = pd.DataFrame()
        self._df_cf = pd.DataFrame()
        self._df_sce = pd.DataFrame()

    def finance(self, 
        corp_code: str, 
        year: int, 
        quarter: int = 4, 
        api_no: int | FinanceStatus = FinanceStatus.SINGLE_COMPANY_MAIN_ACCOUNTS,
        financial_statement: str = "OFS", # OFS:재무제표, CFS:연결재무제표
        financial_statement_type: str = "BS1",
        indicator_code: str | IndexClassCode = IndexClassCode.PROFITABILITY) -> List[Any]:
        """
        OpenDart 정기보고서 재무정보
        corp_code으로만 조회가 가능, stock_code 및 기업명으로는 조회되지 않는다.
        https://opendart.fss.or.kr/guide/main.do?apiGrpCd=DS003
        
        보고서 코드 (reprt_code) : 단일회사 주요계정, 다중회사 주요계정, 단일회사 전체 재무제표, 단일회사 주요 재무지표, 다중회사 주요 재무지표
        1분기보고서 : 11013
        반기보고서 : 11012
        3분기보고서 : 11014
        사업보고서 : 11011

        지표분류코드 (idx_cl_code): 단일회사 주요 재무지표, 다중회사 주요 재무지표
        수익성지표 : M210000
        안정성지표 : M220000
        성장성지표 : M230000
        활동성지표 : M240000

        재무제표구분 (sj_div): XBRL택사노미재무제표양식
        ※재무제표구분 참조

        개별/연결구분 (fs_div): 단일회사 전체 재무제표
        OFS:재무제표
        CFS:연결재무제표

        Args:
            code (str): 기업 고유번호  (주식 코드(stock_code) 및 DART 고유번호 모두 가능(corp_code))
            year (int): 사업연도
            quarter (int): 분기, 사업보고서
        Returns:
            Dict: 기업개황
        """
        if isinstance(api_no, int):
            api_no = FinanceStatus(api_no)

        url = FinanceStatus.url_by_code(api_no.value)
        report_code = quarters.get(str(quarter), "4") 

        request = OpenDartRequest(
            crtfc_key=self.client.api_key,
            corp_code=corp_code,
            bsns_year=year,
            reprt_code=report_code,
        )

        if api_no == FinanceStatus.SINGLE_COMPANY_FINANCIAL_STATEMENT:
            request.fs_div = financial_statement # OFS:재무제표, CFS:연결재무제표
        elif api_no == FinanceStatus.XBRL_TAXONOMY_FINANCIAL_STATEMENT:
            request.sj_div = financial_statement_type # ※재무제표구분 참조
        elif api_no == FinanceStatus.SINGLE_COMPANY_KEY_FINANCIAL_INDICATOR or \
             api_no == FinanceStatus.MULTI_COMPANY_KEY_FINANCIAL_INDICATOR:
            request.idx_cl_code = indicator_code.value

        print(f"URL: {url}, params: {request.to_params()}")
        response = self.client._get(url, params=request.to_params())
        
        json_data = response.json()
        #print(json_data)
            
        status = json_data.get("status")

        # 에러 체크
        if status != "000":
            print(f"Error: {json_data.get('message')}")
            return []

        self.corp_code = json_data.get("corp_code")
        self.corp_name = json_data.get("corp_name")
        self.stock_code = json_data.get("stock_code")

        del json_data["status"]
        del json_data["message"]
        
        print(f"api_type: {api_no.display_name}")
        data_list = json_data.get("list", [])
        if api_no == FinanceStatus.SINGLE_COMPANY_MAIN_ACCOUNTS:
            return [SingleCompanyMainAccountsData(**data) for data in data_list]
        elif api_no == FinanceStatus.MULTI_COMPANY_MAIN_ACCOUNTS:
            return [MultiCompanyMainAccountsData(**data) for data in data_list]
        elif api_no == FinanceStatus.SINGLE_COMPANY_FINANCIAL_STATEMENT:
            return [SingleFinancialStatementData(**data) for data in data_list]
        elif api_no == FinanceStatus.XBRL_TAXONOMY_FINANCIAL_STATEMENT:
            return [XBRLTaxonomyFinancialStatementData(**data) for data in data_list]
        elif api_no == FinanceStatus.SINGLE_COMPANY_KEY_FINANCIAL_INDICATOR:
            return [SingleCompanyKeyFinancialIndicatorData(**data) for data in data_list]
        elif api_no == FinanceStatus.MULTI_COMPANY_KEY_FINANCIAL_INDICATOR:
            return [MultiCompanyKeyFinancialIndicatorData(**data) for data in data_list]

        return []

    def balance_sheet(self, corp_code: str, year: str, quarter: int):
        """OpenDart 정기보고서 재무정보 - 재무상태표"""

        financial_statement = "CFS"
        yearly = True
        if self._df_bs.empty or not (self._df_bs['yearly'] == yearly).any():
            self._financial_statements(corp_code, year, quarter, financial_statement = financial_statement)
        
        df_bs = self._df_bs[(self._df_bs['financial_statement'] == financial_statement) & (self._df_bs['yearly'] == yearly)]
        df_bs.drop(columns=['financial_statement', 'yearly'], inplace=True)
        return df_bs

    def quarterly_balance_sheet(self, corp_code: str, year: str, quarter: int):
        """OpenDart 정기보고서 재무정보 - 재무상태표"""

        financial_statement = "CFS"
        yearly = False
        if self._df_bs.empty or not (self._df_bs['yearly'] == yearly).any():
            self._financial_statements(corp_code, year, quarter, financial_statement = financial_statement, yearly=yearly)
        
        df_bs = self._df_bs[(self._df_bs['financial_statement'] == financial_statement) & (self._df_bs['yearly'] == yearly)]
        df_bs.drop(columns=['financial_statement', 'yearly'], inplace=True)
        return df_bs

    def income_statement(self, corp_code: str, year: str, quarter: int):
        """OpenDart 정기보고서 재무정보 - 손익계산서"""

        financial_statement = "CFS"
        yearly = True
        if self._df_cis.empty or not (self._df_cis['yearly'] == yearly).any():
            self._financial_statements(corp_code, year, quarter, financial_statement = financial_statement)
        
        df_cis = self._df_cis[(self._df_cis['financial_statement'] == financial_statement) & (self._df_cis['yearly'] == yearly)]
        df_cis.drop(columns=['financial_statement', 'yearly'], inplace=True)
        df_is = self._df_is[(self._df_is['financial_statement'] == financial_statement) & (self._df_is['yearly'] == yearly)]
        df_is.drop(columns=['financial_statement', 'yearly'], inplace=True)
        return df_cis, df_is

    def quarterly_income_statement(self, corp_code: str, year: str, quarter: int):
        """OpenDart 정기보고서 재무정보 - 손익계산서"""

        financial_statement = "CFS"
        yearly = False
        if self._df_cis.empty or not (self._df_cis['yearly'] == yearly).any():
            self._financial_statements(corp_code, year, quarter, financial_statement = financial_statement, yearly=yearly)
        
        df_cis = self._df_cis[(self._df_cis['financial_statement'] == financial_statement) & (self._df_cis['yearly'] == yearly)]
        df_cis.drop(columns=['financial_statement', 'yearly'], inplace=True)
        df_is = self._df_is[(self._df_is['financial_statement'] == financial_statement) & (self._df_is['yearly'] == yearly)]
        df_is.drop(columns=['financial_statement', 'yearly'], inplace=True)
        return df_cis, df_is

    def cash_flow(self, corp_code: str, year: str, quarter: int):
        """OpenDart 정기보고서 재무정보 - 현금흐름표"""

        financial_statement = "CFS"
        yearly = True
        if self._df_cf.empty or not (self._df_cf['yearly'] == yearly).any():
            self._financial_statements(corp_code, year, quarter, financial_statement = financial_statement)

        df_cf = self._df_cf[(self._df_cf['financial_statement'] == financial_statement) & (self._df_cf['yearly'] == yearly)]
        df_cf.drop(columns=['financial_statement', 'yearly'], inplace=True)
        return df_cf

    def quarterly_cash_flow(self, corp_code: str, year: str, quarter: int):
        """OpenDart 정기보고서 재무정보 - 현금흐름표"""

        financial_statement = "CFS"
        yearly = False
        if self._df_cf.empty or not (self._df_cf['yearly'] == yearly).any():
            self._financial_statements(corp_code, year, quarter, financial_statement = financial_statement)

        df_cf = self._df_cf[(self._df_cf['financial_statement'] == financial_statement) & (self._df_cf['yearly'] == yearly)]
        df_cf.drop(columns=['financial_statement', 'yearly'], inplace=True)
        return df_cf

    def _financial_statements(self, corp_code: str, year: str, quarter: int, financial_statement: str = "CFS", yearly: bool = True):
        total_cis = []
        total_is = []
        total_bs = []
        total_cf = []
        total_sce = []

        api_no = FinanceStatus.SINGLE_COMPANY_FINANCIAL_STATEMENT
        data = self.finance(corp_code, year, quarter, api_no=api_no, financial_statement=financial_statement)
        if len(data) == 0:
            year = year - 1 if quarter == 1 else year
            quarter = 4 if quarter == 1 else quarter - 1
            data = self.finance(corp_code, year, quarter, api_no=api_no, financial_statement=financial_statement)

        for item in data:
            if item.sj_div == 'CIS':
                total_cis.append(item.to_dict())
            elif item.sj_div == 'IS':
                total_is.append(item.to_dict())
            elif item.sj_div == 'BS':
                total_bs.append(item.to_dict())
            elif item.sj_div == 'CF':
                total_cf.append(item.to_dict())
            elif item.sj_div == 'SCE':
                total_sce.append(item.to_dict())

        if yearly:
            year = year - 1
            quarter = 4
        else:
            year = year - 1 if quarter == 1 else year
            quarter = 4 if quarter == 1 else quarter - 1
        
        data = self.finance(corp_code, year, quarter, api_no=api_no, financial_statement=financial_statement)

        for item in data:
            if item.sj_div == 'CIS':
                total_cis.append(item.to_dict())
            elif item.sj_div == 'IS':
                total_is.append(item.to_dict())
            elif item.sj_div == 'BS':
                total_bs.append(item.to_dict())
            elif item.sj_div == 'CF':
                total_cf.append(item.to_dict())
            elif item.sj_div == 'SCE':
                total_sce.append(item.to_dict())

        if yearly:
            year = year - 1
        else:
            year = year - 1 if quarter == 1 else year
            quarter = 4 if quarter == 1 else quarter - 1
        
        data = self.finance(corp_code, year, quarter, api_no=api_no, financial_statement=financial_statement)
        for item in data:
            if item.sj_div == 'CIS':
                total_cis.append(item.to_dict())
            elif item.sj_div == 'IS':
                total_is.append(item.to_dict())
            elif item.sj_div == 'BS':
                total_bs.append(item.to_dict())
            elif item.sj_div == 'CF':
                total_cf.append(item.to_dict())
            elif item.sj_div == 'SCE':
                total_sce.append(item.to_dict())

        if yearly:
            year = year - 1
        else:
            year = year - 1 if quarter == 1 else year
            quarter = 4 if quarter == 1 else quarter - 1
        
        data = self.finance(corp_code, year, quarter, api_no=api_no, financial_statement=financial_statement)
        for item in data:
            if item.sj_div == 'CIS':
                total_cis.append(item.to_dict())
            elif item.sj_div == 'IS':
                total_is.append(item.to_dict())
            elif item.sj_div == 'BS':
                total_bs.append(item.to_dict())
            elif item.sj_div == 'CF':
                total_cf.append(item.to_dict())
            elif item.sj_div == 'SCE':
                total_sce.append(item.to_dict())

        #print(total_cis)
        #print(total_is)
        #print(total_bs)
        #print(total_cf)
        #print(total_sce)

        df_cis = self._transform_dart_financial_data(total_cis, financial_statement=financial_statement, yearly=yearly)
        df_is = self._transform_dart_financial_data(total_is, financial_statement=financial_statement, yearly=yearly)
        df_bs = self._transform_dart_financial_data(total_bs, financial_statement=financial_statement, yearly=yearly)
        df_cf = self._transform_dart_financial_data(total_cf, financial_statement=financial_statement, yearly=yearly)
        df_sce = self._transform_dart_financial_data(total_sce, financial_statement=financial_statement, yearly=yearly)

        self._df_cis = pd.concat([self._df_cis, df_cis], ignore_index=True)
        self._df_is = pd.concat([self._df_is, df_is], ignore_index=True)
        self._df_bs = pd.concat([self._df_bs, df_bs], ignore_index=True)
        self._df_cf = pd.concat([self._df_cf, df_cf], ignore_index=True)
        self._df_sce = pd.concat([self._df_sce, df_sce], ignore_index=True)

    def _transform_dart_financial_data(self, data: List[Dict[str, Any]], financial_statement: str, yearly: bool) -> pd.DataFrame:
        """
        DART API 응답 데이터(List[Dict])를 피벗된 DataFrame으로 변환합니다.

        1분기보고서 : 11013
        반기보고서 : 11012
        3분기보고서 : 11014
        사업보고서 : 11011
        
        Parameters
        ----------
        data : List[Dict[str, Any]]
            DART API에서 반환된 재무제표 데이터
            
        Returns
        -------
        pd.DataFrame
            account_nm을 인덱스로, 연도/분기별 금액을 컬럼으로 가진 DataFrame
        """
        df = pd.DataFrame(data)
        
        # 금액 컬럼 숫자 변환
        amount_cols = ['thstrm_amount', 'thstrm_add_amount', 'frmtrm_amount', 
                    'frmtrm_q_amount', 'frmtrm_add_amount', 'bfefrmtrm_amount']
        for col in amount_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 기간 컬럼명 생성 함수
        def get_period_label(reprt_code: str, bsns_year: str) -> str:
            """reprt_code와 bsns_year로 기간 라벨 생성"""
            code_to_quarter = {
                '11013': '03',  # 1분기
                '11012': '06',  # 반기
                '11014': '09',  # 3분기
                '11011': '12',  # 사업보고서
            }
            quarter = code_to_quarter.get(reprt_code, '12')
            return f"{bsns_year}/{quarter}"
        
        # 계정명 정규화 함수
        def normalize_account_nm(name: str) -> str:
            """계정명에서 주석 제거 및 통합"""
            if pd.isna(name):
                return name
            # (*3), (*4) 등 주석 제거
            name = re.sub(r'\(\*\d+\)', '', name).strip()
            # 계정명 통합
            name_mapping = {
                '당기순이익(손실)': '당기순이익',
                '분기순이익': '당기순이익',
                '분기총포괄손익': '총포괄손익',
                '당기손익으로 재분류되는 세후기타포괄손익': '후속적으로 당기손익으로 재분류되는 포괄손익',
            }
            return name_mapping.get(name, name)

        def format_amount(value, unit: int = 100_000_000) -> str:
            """
            금액을 단위로 나누고 천단위 콤마 포맷으로 변환합니다.
            
            Parameters
            ----------
            value : float or int
                원본 금액 (원 단위)
            unit : int
                나눌 단위 (기본값: 1억 = 100,000,000)
                
            Returns
            -------
            str
                포맷된 문자열 (예: "207,114")
            """
            if pd.isna(value):
                return ''
            return f"{round(value / unit):,}"
        
        # 계정명 정규화
        df['account_nm_norm'] = df['account_nm'].apply(normalize_account_nm)
        
        # 기간 라벨 생성
        df['period'] = df.apply(lambda x: get_period_label(x['reprt_code'], x['bsns_year']), axis=1)
        
        # 결과 저장용 딕셔너리
        result_data = {}
        
        # 각 행 처리
        for _, row in df.iterrows():
            account = row['account_nm_norm']
            period = row['period']
            
            if account not in result_data:
                result_data[account] = {}
            
            # thstrm_amount (당기)
            unit = 100_000_000
            if pd.notna(row['thstrm_amount']):
                result_data[account][period] = format_amount(row['thstrm_amount'])
            
            # thstrm_add_amount (당기 누적) - 분기 보고서만 해당
            if pd.notna(row['thstrm_add_amount']) and row['reprt_code'] != '11011':
                result_data[account][f"{period}(+)"] = format_amount(row['thstrm_add_amount'])
        
        # DataFrame 생성
        result_df = pd.DataFrame(result_data).T
        print(result_df)
        
        # 컬럼 정렬 (최신 연도/분기 우선)
        def sort_key(col: str) -> tuple:
            """컬럼 정렬 키 생성"""
            is_cumulative = '(+)' in col
            base_col = col.replace('(+)', '')
            year, month = base_col.split('/')
            # 연도 내림차순, 월 내림차순, 누적은 기본 뒤에
            return (-int(year), -int(month), is_cumulative)
        
        sorted_cols = sorted(result_df.columns, key=sort_key)
        result_df = result_df[sorted_cols]
        
        # 행 순서 정의
        row_order = [
            '총포괄손익',
            '비지배지분',
            '지배기업 소유주지분',
            '기타포괄손익',
            '후속적으로 당기손익으로 재분류되는 포괄손익',
            '현금흐름위험회피파생상품평가손익',
            '해외사업장환산외환차이',
            '관계기업 및 공동기업의 기타포괄손익에 대한 지분',
            '후속적으로 당기손익으로 재분류되지 않는 포괄손익',
            '기타포괄손익-공정가치금융자산평가손익',
            '순확정급여부채(자산) 재측정요소',
            '당기순이익',
        ]
        
        # 존재하는 행만 순서대로 정렬
        #existing_rows = [r for r in row_order if r in result_df.index]
        #remaining_rows = [r for r in result_df.index if r not in row_order]
        #result_df = result_df.loc[existing_rows + remaining_rows]
        
        # 인덱스명 설정
        #result_df.index.name = 'IFRS'

        result_df['financial_statement'] = financial_statement
        result_df['yearly'] = yearly

        result_df = result_df.reset_index()
        
        return result_df

    def finance_file(self, rcept_no, report_code: str = None, quarter: int = 4, save_path: str | None = None):
        """
        OpenDart 정기보고서 재무정보 - 재무제표 원본파일(XBRL)

        상장법인(유가증권, 코스닥) 및 주요 비상장법인(사업보고서 제출대상 & IFRS 적용)이 제출한 정기보고서 내에 XBRL재무제표의 원본파일(XBRL)을 제공합니다.
        https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS003&apiId=2019019

        Args:
            rcept_no (str): 접수번호
            quarter (int): 분기, 사업보고서
            save_path (str): 파일 저장 경로
        Returns:
            pd.DataFrame: 기업개황
        """

        api_no = FinanceStatus.FINANCIAL_STATEMENT_ORIGINAL_FILE_XBRL
        url = FinanceStatus.url_by_code(api_no.value)
        report_code = report_code or quarters.get(str(quarter), "4")
        
        params = {
            "crtfc_key": self.client.api_key,
            "rcept_no": rcept_no,
            "reprt_code": report_code
        }

        response = self.client._get(url, params=params)
        response_headers = response.headers
        print(response_headers)

        if response.status_code != 200:
            print(f"다운로드 실패: {response.status_code}")
            return None

        content_type = response_headers.get("Content-Type")
        if "application/xml" in content_type or "application/json" in content_type:
            text_data = response.text
            print(text_data)
            return None

        # 바이너리 데이터 
        binary_data = response.content
        #print(binary_data)
        
        if save_path is None:
            save_path = f"dart_{rcept_no}"
            save_path = save_zip_path(response_headers, save_path)

        # ZIP 파일 저장
        #save_zip(binary_data, save_path)
        # ZIP 파일 압축해제 및 폴더에 저장
        save_unzip(binary_data, save_path)
        return save_path

    def _parse_xml(self, xml_content, filename=None):
        """
        XML 내용 파싱
        Args:
            xml_content (bytes): XML 바이너리 내용
            filename (str): 파일명
        Returns:
            dict: 파싱된 데이터
        """
        from bs4 import BeautifulSoup
        
        # bytes를 str로 변환
        xml_str = None
        for encoding in ['utf-8', 'euc-kr', 'cp949']:
            try:
                xml_str = xml_content.decode(encoding)
                break
            except:
                continue
        
        if xml_str is None:
            return {'filename': filename, 'error': '인코딩 실패'}
        
        soup = BeautifulSoup(xml_str, 'lxml-xml')
        
        result = {
            'filename': filename,
            'title': None,
            'tables': [],
            'text_content': None,
            'list': []
        }
        
        # 제목 추출
        title_tag = soup.find('TITLE') or soup.find('title')
        if title_tag:
            result['title'] = title_tag.get_text(strip=True)
        
        # 테이블 추출
        tables = soup.find_all('TABLE') or soup.find_all('table')
        for idx, table in enumerate(tables):
            rows = []
            for tr in table.find_all(['TR', 'tr']):
                row = []
                for cell in tr.find_all(['TD', 'TH', 'td', 'th']):
                    text = cell.get_text(separator=' ', strip=True)
                    text = re.sub(r'\s+', ' ', text)
                    row.append(text)
                if row:
                    rows.append(row)
            
            if rows:
                # DataFrame으로 변환
                df = self._rows_to_dataframe(rows)
                
                result['tables'].append({
                    'index': idx,
                    'data': rows,
                    'dataframe': df
                })
        
        # 텍스트 내용 추출
        body = soup.find('BODY') or soup.find('body')
        if body:
            result['text_content'] = body.get_text(separator='\n', strip=True)

        # list 태그들 추출
        result_list = soup.find('result')
        if result_list:
            data = []
            for item in result_list.find_all('list'):
                # XML을 JSON 리스트로 변환
                row = {child.name: child.get_text(strip=True) for child in item.children if child.name}
                data.append(row)
            result['list'] = data
        
        return result

    def _to_dataframe(self, data: list[dict]) -> pd.DataFrame:
        """
        DART 재무제표 API 응답을 DataFrame으로 변환
        금액 컬럼을 숫자로 변환하는 전처리 포함
        """
        df = pd.DataFrame(data)
        
        # 금액 컬럼을 숫자로 변환
        amount_columns = ['thstrm_amount', 'thstrm_add_amount', 'frmtrm_amount', 'bfefrmtrm_amount']
        for col in amount_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # ord 컬럼을 정수로 변환
        if 'ord' in df.columns:
            df['ord'] = pd.to_numeric(df['ord'], errors='coerce').astype('Int64')
        
        # 정렬
        df = df.sort_values(['bsns_year', 'reprt_code', 'ord'], ascending=[False, False, True])
        
        return df.reset_index(drop=True)

    def _rows_to_dataframe(self, rows):
        """
        2D 리스트를 DataFrame으로 안전하게 변환
        """
        if not rows:
            return pd.DataFrame()
        
        if len(rows) == 1:
            return pd.DataFrame(rows)
        
        # 최대 컬럼 수 계산
        max_cols = max(len(row) for row in rows)
        
        # 모든 행의 길이를 최대 컬럼 수에 맞춤
        normalized = []
        for row in rows:
            if len(row) < max_cols:
                row = row + [''] * (max_cols - len(row))
            normalized.append(row)
        
        # 첫 행을 헤더로 사용
        header = normalized[0]
        data = normalized[1:]
        
        # 빈 헤더 처리
        header = [f"col_{i}" if not h else h for i, h in enumerate(header)]
        
        # 헤더 중복 처리
        seen = {}
        unique_header = []
        for col in header:
            if col in seen:
                seen[col] += 1
                unique_header.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 0
                unique_header.append(col)
        
        return pd.DataFrame(data, columns=unique_header)
