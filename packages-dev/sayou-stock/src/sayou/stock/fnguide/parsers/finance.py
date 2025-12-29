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
 
import logging
import pandas as pd
import requests

from bs4 import BeautifulSoup, Tag
from typing import Dict, List, Tuple, Optional, Any

from ..client import FnGuideClient

from ..utils import (
    FNGUIDE_URLS,
)

from .tables import (
    TableFinder,
    HeaderExtractor,
    BodyExtractor
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FnGuideFinanceParser:
    """
    FnGuide 재무제표 파싱 클래스
    
    재무제표, https://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?gicode=A{stock}&ReportGB=D
    """

    finance_table_titles = ["포괄손익계산서", "재무상태표", "현금흐름표"]
    FINANCE_TABLE_IDS = ["divSonikY", "divSonikQ", "divDaechaY", "divDaechaQ", "divCashY", "divCashQ"]

    def __init__(self, client: FnGuideClient, debug: bool = False):
        self.client = client

        self._income_statement = pd.DataFrame()
        self._quarterly_income_statement = pd.DataFrame()
        self._balance_sheet = pd.DataFrame()
        self._quarterly_balance_sheet = pd.DataFrame()
        self._cash_flow = pd.DataFrame()
        self._quarterly_cash_flow = pd.DataFrame()

        self.debug = debug
        self.table_finder = TableFinder()
        self.header_extractor = HeaderExtractor()
    
    def parse(self, stock: str, report_type: str = "D"):
        """
        기업 정보 | 재무제표 정보 추출 후 주요 키를 영어로 변환
        requests로 HTML을 가져온 후 pandas.read_html()로 파싱

        재무제표 3종(포괄손익계산서, 재무상태표, 현금흐름표)을
        requests와 BeautifulSoup으로 크롤링하여 멀티인덱스 DataFrame으로 구조화

        Args:
            stock: 종목 코드 (회사명을 "company"로 치환하기 위해 사용)
            report_type: 재무제표 유형 (D: 연간, B: 분기)

        Returns:
            {테이블명: 레코드_리스트} 딕셔너리
        """

        url = FNGUIDE_URLS.get("재무제표")

        if not url:
            return
        
        params = {
            "gicode": f"A{stock}",
            "ReportGB": report_type or "D" # D: 연간, B: 분기
        }

        try:
            response = self.client._get(url, params=params)
        except requests.RequestException as e:
            logger.error(f"페이지 요청 실패: {e}")
            return None

        # 테이블 파싱
        result_dict = []
        
        tables = self._parse_tables(response.text, self.FINANCE_TABLE_IDS)
        for key, table in tables.items():
            records = self._dataframe_to_records(table)

            # "포괄손익계산서", "재무상태표", "현금흐름표"]
            if key == "divSonikY":
                key_name = "포괄손익계산서"
                key_type = "연간"
                self._income_statement = table
            elif key == "divSonikQ":
                key_name = "포괄손익계산서"
                key_type = "분기"
                self._quarterly_income_statement = table
            elif key == "divDaechaY":
                key_name = "재무상태표"
                key_type = "연간"
                self._balance_sheet = table
            elif key == "divDaechaQ":
                key_name = "재무상태표"
                key_type = "분기"
                self._quarterly_balance_sheet = table
            elif key == "divCashY":
                key_name = "현금흐름표"
                key_type = "연간"
                self._cash_flow = table
            elif key == "divCashQ":
                key_name = "현금흐름표"
                key_type = "분기"
                self._quarterly_cash_flow = table

            record = {
                "key_name": key_name,
                "key_type": key_type,
                "key": key,
                "records": records
            }
            result_dict.append(record)
        
        return result_dict

    def income_statement(self, stock: str) -> pd.DataFrame:
        """Fetch income statement (연간 포괄손익계산서)"""
        if self._income_statement is None or \
            self._income_statement.empty:
            self._income_statement = self.parse(stock=stock)
        return self._income_statement
    
    def quarterly_income_statement(self, stock: str) -> pd.DataFrame:
        """Fetch quarterly income statement (분기별 포괄손익계산서)"""
        if self._quarterly_income_statement is None or \
            self._quarterly_income_statement.empty:
            self._quarterly_income_statement = self.parse(stock=stock)
        return self._quarterly_income_statement
    
    def balance_sheet(self, stock: str) -> pd.DataFrame:
        """Fetch balance sheet (연간 재무상태표)"""
        if self._balance_sheet is None or \
            self._balance_sheet.empty:
            self._balance_sheet = self.parse(stock=stock)
        return self._balance_sheet
    
    def quarterly_balance_sheet(self, stock: str) -> pd.DataFrame:
        """Fetch quarterly balance sheet (분기별 재무상태표)"""
        if self._quarterly_balance_sheet is None or \
            self._quarterly_balance_sheet.empty:
            self._quarterly_balance_sheet = self.parse(stock=stock)
        return self._quarterly_balance_sheet
    
    def cash_flow(self, stock: str) -> pd.DataFrame:
        """Fetch cash flow (연간 현금흐름표)"""
        if self._cash_flow is None or \
            self._cash_flow.empty:
            self._cash_flow = self.parse(stock=stock)
        return self._cash_flow
    
    def quarterly_cash_flow(self, stock: str) -> pd.DataFrame:
        """Fetch quarterly cash flow (분기별 현금흐름표)"""
        if self._quarterly_cash_flow is None or \
            self._quarterly_cash_flow.empty:
            self._quarterly_cash_flow = self.parse(stock=stock)
        return self._quarterly_cash_flow    
    
    def _parse_tables(
        self,
        html_text: str,
        ids: list
    ) -> Optional[pd.DataFrame]:
        """
        단일 테이블 파싱
        
        Args:
            soup: BeautifulSoup 객체
            title: 테이블 제목
        
        Returns:
            DataFrame 또는 None
        """
        logger.info(f"\n테이블 데이터 수집 중...")

        soup = BeautifulSoup(html_text, "html.parser")
        
        # 1. 테이블 찾기
        tables = self.table_finder.find_by_ids(soup, ids)
        if len(tables) == 0:
            return None
        
        for key, table in tables.items():
            df = self._parse_table(table)
            tables[key] = df
        
        return tables
    
    def parse_table_by_title(
        self,
        soup: BeautifulSoup,
        title: str
    ) -> Optional[pd.DataFrame]:
        """
        단일 테이블 파싱
        
        Args:
            soup: BeautifulSoup 객체
            title: 테이블 제목
        
        Returns:
            DataFrame 또는 None
        """
        logger.info(f"\n{title} 데이터 수집 중...")
        
        # 1. 테이블 찾기
        table = self.table_finder.find_by_title(soup, title)
        if not table:
            return None
        
        return self._parse_table(table)
        
    def _parse_table(
        self,
        table: Tag
    ) -> Optional[pd.DataFrame]:
        """
        단일 테이블 파싱
        
        Args:
            soup: BeautifulSoup 객체
            title: 테이블 제목
        
        Returns:
            DataFrame 또는 None
        """
        logger.info(f"\n테이블 데이터 수집 중...")
        table_id = table.get("id")
        
        if not table:
            return None
        
        # 1. thead 추출
        thead = table.find("thead")
        if not thead:
            logger.warning("thead를 찾을 수 없음")
            return None
        
        # 2. 헤더 인덱스 추출
        headers = self.header_extractor.extract_headers(thead)
        if not headers:
            logger.warning("인덱스 리스트가 비어있음")
            return None
        
        # 3. tbody 추출
        tbody = table.find("tbody")
        if not tbody:
            logger.warning("tbody를 찾을 수 없음")
            return None
       
        # 4. 데이터 딕셔너리 추출
        body_extractor = BodyExtractor(debug=self.debug)
        data_dict = body_extractor.extract(tbody, headers)
        
        if not data_dict:
            logger.warning("데이터가 비어있음")
            return None
        
        # 5. DataFrame 생성
        df = self._create_dataframe(data_dict, headers)
        
        logger.info(f"완료! DataFrame shape: {df.shape}")
        
        return df
        
    def _dataframe_to_records(self, frame: pd.DataFrame) -> list[dict[str, Any]]:
        """
        DataFrame을 JSON 직렬화를 위한 레코드 리스트로 변환한다.
    
        멀티인덱스 컬럼은 " / "로 결합된 단일 키로 변환하고,
        인덱스(기간)는 'period' 필드로 포함한다.
        """
        if frame is None or frame.empty:
            return []
    
        flattened_columns = [self._flatten_column_key(col) for col in frame.columns]
        records: list[dict[str, Any]] = []
    
        for index_label, row in frame.iterrows():
            record: dict[str, Any] = {"period": str(index_label)}
            for key, value in zip(flattened_columns, row.tolist()):
                if key in record:
                    suffix = 2
                    new_key = f"{key}_{suffix}"
                    while new_key in record:
                        suffix += 1
                        new_key = f"{key}_{suffix}"
                    record[new_key] = value
                else:
                    record[key] = value
            records.append(record)
    
        return records

    @staticmethod
    def _create_dataframe(
        data_dict: Dict[Tuple[str, str], List[str]],
        index_list: List[str]
    ) -> pd.DataFrame:
        """
        데이터 딕셔너리에서 DataFrame 생성
        
        Args:
            data_dict: {(카테고리, 항목): [값들]} 딕셔너리
            index_list: 인덱스 리스트
        
        Returns:
            멀티인덱스 컬럼을 가진 DataFrame
        """
        df = pd.DataFrame(data_dict, index=index_list)
        
        # 멀티인덱스로 컬럼 변환
        #df.columns = pd.MultiIndex.from_tuples(df.columns)
        
        return df

    @staticmethod
    def _flatten_column_key(column: Any) -> str:
        """
        멀티인덱스 컬럼 키를 JSON 직렬화가 가능한 단일 문자열로 변환한다.
        """
        if isinstance(column, tuple):
            parts = [str(part).strip() for part in column if part not in (None, "")]
            key = " / ".join(parts)
        elif column is None:
            key = ""
        else:
            key = str(column).strip()
    
        return key or "value"
