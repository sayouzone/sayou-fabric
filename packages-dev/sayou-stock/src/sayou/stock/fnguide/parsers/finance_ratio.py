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

from ..models import FinancialRatioData

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

class FnGuideFinanceRatioParser:
    """
    FnGuide 재무비율 파싱 클래스
    
    재무비율, https://comp.fnguide.com/SVO2/ASP/SVD_FinanceRatio.asp?gicode=A{stock}&ReportGB=D
    """

    def __init__(self, client: FnGuideClient):
        self.client = client

        self.table_finder = TableFinder()
        self.header_extractor = HeaderExtractor()
    
    def parse(self, stock: str, report_type: str = "D"):
        """
        기업 정보 | 재무비율 정보 추출 후 주요 키를 영어로 변환
        requests로 HTML을 가져온 후 pandas.read_html()로 파싱

        Args:
            html_text (str): HTML text
            stock: 종목 코드 (회사명을 "company"로 치환하기 위해 사용)

        Returns:
            Dict: 컬럼명이 번역된 DataFrame
        """

        url = FNGUIDE_URLS.get("재무비율")

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

        soup = BeautifulSoup(response.text, "html.parser")

        # 테이블 파싱
        output = {}
        
        results = self._parse_tables(soup)

        for idx, data in enumerate(results):
            #print(idx, data)
            if not data.periods:
                continue
            
            output[idx] = data

        return output
    
    def _parse_tables(
        self,
        soup: BeautifulSoup
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
        
        # 1. 테이블 찾기
        tables = self.table_finder.find(soup)
        if len(tables) == 0:
            return []
        
        results = []
        for table in tables:
            #print(table, type(table))
            result = self._parse_table(table)
            results.append(result)
        
        return results
        
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
        
        if not table:
            return None

        result = FinancialRatioData()
        
        # 1. thead 추출
        thead = table.find("thead")
        if thead:
            result.periods = self.header_extractor.extract_headers(thead)
        
        # 2. tbody 추출
        tbody = table.find("tbody")
        if tbody:
            body_extractor = BodyExtractor(include_hidden=True)
            result.data = body_extractor.extract(tbody, result.periods)
        
        logger.info(f"완료! {result}")
        
        return result

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
        df.columns = pd.MultiIndex.from_tuples(df.columns)
        
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
