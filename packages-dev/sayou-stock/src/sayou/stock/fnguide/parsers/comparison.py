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
from typing import Dict, List, Tuple, Optional, Any, Union

from ..client import FnGuideClient

from ..utils import (
    FNGUIDE_URLS
)

from ..models import (
    TableData,
    KeyValueData,
    HistoryData
)

from .tables import (
    TableFinder,
    HeaderExtractor,
    BodyExtractor,
    KeyValueExtractor,
    HistoryExtractor
)

from .json_parser import FnGuideJsonParser

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FnGuideComparisonParser:
    """
    FnGuide 경쟁사비교 파싱 클래스
    
    경쟁사비교, https://comp.fnguide.com/SVO2/ASP/SVD_Comparison.asp?gicode=A{stock}
    """

    # 테이블 유형 판별용 caption 패턴
    KEY_VALUE_CAPTIONS = {}

    JSON_URLS = {
        "임직원 정보": "https://comp.fnguide.com/SVO2/json/data/09/A{stock}.json?_={timestamp}"
    }

    def __init__(self, client: FnGuideClient):
        self.client = client

        self.include_hidden = False
        self.use_category = True
        self.debug = False

        self.parser = FnGuideJsonParser()
    
    def parse(self, stock: str, report_type: str = "D"):
        """
        기업 정보 | 경쟁사비교 정보 추출 후 주요 키를 영어로 변환
        requests로 HTML을 가져온 후 pandas.read_html()로 파싱

        Args:
            html_text (str): HTML text
            stock: 종목 코드 (회사명을 "company"로 치환하기 위해 사용)

        Returns:
            Dict: 컬럼명이 번역된 DataFrame
        """

        url = FNGUIDE_URLS.get("경쟁사비교")

        if not url:
            return
        
        params = {
            "gicode": f"A{stock}",
            "ReportGB": report_type or "D" # D: 연결, B: 별도
        }

        try:
            response = self.client._get(url, params=params)
        except requests.RequestException as e:
            logger.error(f"페이지 요청 실패: {e}")
            return None

        results = self._parse_by_caption(response.text)

        referer_url = response.url
        for key, url in self.JSON_URLS.items():
            # 1. Asia/Seoul 타임존의 현재 시간 가져오기
            now_seoul = pd.Timestamp.now(tz='Asia/Seoul')
            ts_seconds = now_seoul.timestamp()
            ts_milliseconds = int(now_seoul.timestamp() * 1000)

            url = url.format(stock=stock, timestamp=ts_milliseconds)
            print("URL:", url)
            value = results.get(key)
            if value:
                continue

            try:
                response = self.client._get(url, referer=referer_url)
            except requests.RequestException as e:
                logger.error(f"페이지 요청 실패: {e}")
                continue
            value = response.json()
            
            df = self.parser.to_dataframe(value)
            results[key] = df

        return results

    def _parse_by_caption(
        self,
        html: str | Tag
    ) -> Dict[str, Union[TableData, KeyValueData]]:
        """
        Caption을 키로 하는 딕셔너리 반환
        
        Returns:
            {caption: 테이블데이터} 딕셔너리
        """
        results = self._parse_all(html)
        return {r.caption: r for r in results if r.caption}

    def _parse_all(
        self,
        html: str | Tag
    ) -> List[Union[TableData, KeyValueData]]:
        """
        HTML에서 모든 테이블 파싱
        
        Returns:
            테이블 데이터 리스트 (유형별 다른 클래스)
        """
        soup = (
            html if isinstance(html, (Tag, BeautifulSoup))
            else BeautifulSoup(html, "html.parser")
        )
        
        tables = soup.find_all("table", class_=lambda x: x and "us_table_ty1" in x)
        results = []
        
        for idx, table in enumerate(tables):
            logger.info(f"테이블 {idx + 1}/{len(tables)} 파싱 중...")
            
            result = self._parse_table(table)
            if result:
                results.append(result)
        
        return results

    def _parse_table(
        self,
        table: Tag
    ) -> Optional[Union[TableData, KeyValueData]]:
        """단일 테이블 파싱 (유형 자동 판별)"""
        
        # Caption 추출
        caption_tag = table.find("caption")
        caption = caption_tag.get_text(strip=True) if caption_tag else ""
        
        # 유형 판별
        if caption in self.KEY_VALUE_CAPTIONS or self._is_key_value_table(table):
            return self._parse_key_value_table(table, caption)
        
        # 기본: 일반 데이터 테이블
        return self._parse_data_table(table, caption)
    
    def _is_key_value_table(self, table: Tag) -> bool:
        """키-값 테이블인지 확인"""
        tbody = table.find("tbody")
        if not tbody:
            return False
        
        # thead 없고, 각 행에 th-td 쌍이 있으면 키-값
        thead = table.find("thead")
        if thead:
            return False
        
        first_tr = tbody.find("tr")
        if not first_tr:
            return False
        
        ths = first_tr.find_all("th", recursive=False)
        tds = first_tr.find_all("td", recursive=False)
        
        # th와 td가 비슷한 개수면 키-값 형태
        return len(ths) >= 1 and len(tds) >= 1 and len(ths) == len(tds)
    
    def _is_history_table(self, table: Tag) -> bool:
        """연혁 테이블인지 확인"""
        thead = table.find("thead")
        if not thead:
            return False
        
        # 날짜, 구분, 내용 같은 헤더가 있으면 연혁
        headers_text = thead.get_text()
        return "날짜" in headers_text or "내용" in headers_text
    
    def _parse_data_table(self, table: Tag, caption: str) -> Optional[TableData]:
        """일반 데이터 테이블 파싱"""
        result = TableData(caption=caption)
        
        # 헤더 추출
        thead = table.find("thead")
        if thead:
            result.headers = HeaderExtractor.extract_headers(thead)
        
        if not result.headers:
            return None
        
        # 바디 추출
        tbody = table.find("tbody")
        if tbody:
            extractor = BodyExtractor(
                include_hidden=self.include_hidden,
                use_category=self.use_category,
                debug=self.debug
            )
            
            if self.use_category:
                result.data_with_category = extractor.extract(tbody, result.headers)
            else:
                result.data = extractor.extract(tbody, result.headers)
        
        # 데이터 없으면 None
        if not result.data and not result.data_with_category:
            return None
        
        return result
    
    def _parse_key_value_table(self, table: Tag, caption: str) -> Optional[KeyValueData]:
        """키-값 테이블 파싱"""
        tbody = table.find("tbody")
        if not tbody:
            return None
        
        extractor = KeyValueExtractor()
        data = extractor.extract(tbody)
        
        if not data:
            return None
        
        return KeyValueData(caption=caption, data=data)
