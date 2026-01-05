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

    def income_statement(self, corp_code: str, year: str, quarter: int):
        """OpenDart 정기보고서 재무정보 - 손익계산서"""

        financial_statement="CFS"

        total_cis = []
        total_is = []
        total_bs = []
        total_cf = []

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

        year = year - 1
        quarter = 4
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

        year = year - 1
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

        year = year - 1
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
        
        df_cis = self._to_dataframe(total_cis)
        df_is = self._to_dataframe(total_is)
        df_bs = self._to_dataframe(total_bs)
        df_cf = self._to_dataframe(total_cf)

        print(df_cis.columns)

        drop_columns = ['rcept_no', 'corp_code', 'corp_cls', 'corp_name', 'stock_code', 'fs_div', 'fs_nm', 'sj_div', 'sj_nm', 'account_id', 'account_detail', 'currency', 'frmtrm_nm', 'frmtrm_amount', 'frmtrm_q_nm', 'frmtrm_q_amount', 'frmtrm_add_amount', 'bfefrmtrm_nm', 'bfefrmtrm_amount']
        drop_columns = ['rcept_no', 'corp_code', 'corp_cls', 'corp_name', 'stock_code', 'fs_div', 'sj_div', 'fs_nm', 'sj_nm', 'account_id', 'account_detail', 'currency', 'thstrm_nm', 'frmtrm_nm', 'frmtrm_amount', 'frmtrm_q_nm', 'frmtrm_q_amount', 'frmtrm_add_amount', 'bfefrmtrm_nm', 'bfefrmtrm_amount']
        df_cis.drop(drop_columns, axis=1, inplace=True)
        df_is.drop(drop_columns, axis=1, inplace=True)
        df_bs.drop(drop_columns, axis=1, inplace=True)
        df_cf.drop(drop_columns, axis=1, inplace=True)

        print(df_cis.columns)

        df_cis = df_cis.set_index(['bsns_year', 'ord'])
        df_is = df_is.set_index(['bsns_year', 'ord'])
        df_bs = df_bs.set_index(['bsns_year', 'ord'])
        df_cf = df_cf.set_index(['bsns_year', 'ord'])


        return df_cis, df_is, df_bs, df_cf

    def quarterly_income_statement(self, corp_code: str, year: str, quarter: int):
        """OpenDart 정기보고서 재무정보 - 손익계산서"""

        financial_statement="CFS"

        total_cis = []
        total_is = []
        total_bs = []
        total_cf = []

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
        
        df_cis = self._to_dataframe(total_cis)
        df_is = self._to_dataframe(total_is)
        df_bs = self._to_dataframe(total_bs)
        df_cf = self._to_dataframe(total_cf)

        df_cis.drop(['rcept_no', 'corp_code', 'corp_cls', 'corp_name', 'reprt_code', 'bsns_year', 'fs_div', 'sj_div', 'currency', 'bfefrmtrm_nm', 'bfefrmtrm_amount'], axis=1, inplace=True)
        df_is.drop(['rcept_no', 'corp_code', 'corp_cls', 'corp_name', 'reprt_code', 'bsns_year', 'fs_div', 'sj_div', 'currency', 'bfefrmtrm_nm', 'bfefrmtrm_amount'], axis=1, inplace=True)
        df_bs.drop(['rcept_no', 'corp_code', 'corp_cls', 'corp_name', 'reprt_code', 'bsns_year', 'fs_div', 'sj_div', 'currency', 'bfefrmtrm_nm', 'bfefrmtrm_amount'], axis=1, inplace=True)
        df_cf.drop(['rcept_no', 'corp_code', 'corp_cls', 'corp_name', 'reprt_code', 'bsns_year', 'fs_div', 'sj_div', 'currency', 'bfefrmtrm_nm', 'bfefrmtrm_amount'], axis=1, inplace=True)

        df_cis = df_cis.set_index('ord')
        df_is = df_is.set_index('ord')
        df_bs = df_bs.set_index('ord')
        df_cf = df_cf.set_index('ord')

        return df_cis, df_is, df_bs, df_cf

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
