import logging
import pandas as pd
import requests

from bs4 import BeautifulSoup, Tag
from typing import Dict, List, Tuple, Optional, Any

from ..client import FnGuideClient

from ..utils import (
    urls
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FnGuideFinanceParser:
    """
    FnGuide 재무제표 파싱 클래스
    
    Snapshot, https://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?gicode=A{stock}
    """

    finance_table_titles = ["포괄손익계산서", "재무상태표", "현금흐름표"]

    def __init__(self, client: FnGuideClient, debug: bool = False):
        self.client = client

        self.debug = debug
        self.table_finder = TableFinder()
        self.header_extractor = HeaderExtractor()
    
    def parse(self, stock: str):
        """
        기업 정보 | 재무제표 정보 추출 후 주요 키를 영어로 변환
        requests로 HTML을 가져온 후 pandas.read_html()로 파싱

        재무제표 3종(포괄손익계산서, 재무상태표, 현금흐름표)을
        requests와 BeautifulSoup으로 크롤링하여 멀티인덱스 DataFrame으로 구조화

        Args:
            html_text (str): HTML text
            stock: 종목 코드 (회사명을 "company"로 치환하기 위해 사용)

        Returns:
            {테이블명: 레코드_리스트} 딕셔너리
        """

        url = urls.get("재무제표")

        if not url:
            return
        
        params = {
            "gicode": f"A{stock}"
        }

        try:
            response = self.client._get(url, params=params)
        except requests.RequestException as e:
            logger.error(f"페이지 요청 실패: {e}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # 테이블 파싱
        result_dict = {}
        
        for title in self.finance_table_titles:
            try:
                df = self.parse_table(soup, title)
                
                if df is not None:
                    # DataFrame을 레코드로 변환
                    result_dict[title] = self._dataframe_to_records(df)
                    #print(result_dict[title])
                else:
                    result_dict[title] = []
            
            except Exception as e:
                logger.error(f"{title} 수집 실패: {e}")
                result_dict[title] = []
        
        return result_dict
    
    def parse_table(
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
        
        # 2. thead 추출
        thead = table.find("thead")
        if not thead:
            logger.warning("thead를 찾을 수 없음")
            return None
        
        # 3. 헤더 인덱스 추출
        index_list = self.header_extractor.extract_index_list(thead)
        if not index_list:
            logger.warning("인덱스 리스트가 비어있음")
            return None
        
        # 4. tbody 추출
        tbody = table.find("tbody")
        if not tbody:
            logger.warning("tbody를 찾을 수 없음")
            return None
        
        # 5. 데이터 딕셔너리 추출
        body_extractor = BodyExtractor(debug=self.debug)
        data_dict = body_extractor.extract(tbody, index_list)
        
        if not data_dict:
            logger.warning("데이터가 비어있음")
            return None
        
        # 6. DataFrame 생성
        df = self._create_dataframe(data_dict, index_list)
        
        logger.info(f"완료! DataFrame shape: {df.shape}")
        
        return df
        
    def _dataframe_to_records(self, frame: pd.DataFrame) -> list[dict[str, Any]]:
        """
        DataFrame을 JSON 직렬화를 위한 레코드 리스트로 변환한다.
    
        멀티인덱스 컬럼은 " / "로 결합된 단일 키로 변환하고,
        인덱스(기간)는 'period' 필드로 포함한다.
        """
        if frame.empty:
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


class TableFinder:
    """테이블 검색 클래스"""
    
    @staticmethod
    def find_by_title(soup: BeautifulSoup, title: str) -> Optional[Tag]:
        """제목으로 테이블 찾기"""
        for table in soup.find_all("table"):
            if title in table.get_text():
                logger.info(f"'{title}' 테이블 발견")
                return table
        
        logger.warning(f"'{title}' 테이블을 찾을 수 없음")
        return None


class HeaderExtractor:
    """테이블 헤더 추출 클래스"""
    
    @staticmethod
    def extract_index_list(thead: Tag) -> List[str]:
        """
        thead에서 인덱스 리스트 추출
        
        Args:
            thead: thead 태그
        
        Returns:
            인덱스 리스트 (날짜/기간 데이터)
        """
        thead_rows = thead.find_all("tr")
        index_rows: List[List[str]] = []
        
        for tr in thead_rows:
            row_headers = HeaderExtractor._extract_row_headers(tr)
            if row_headers:
                index_rows.append(row_headers)
        
        # 가장 긴 행을 선택 (가장 상세한 헤더)
        index_list = max(index_rows, key=len) if index_rows else []
        
        total_headers = sum(len(tr.find_all("th")) for tr in thead_rows)
        logger.info(f"기간 데이터 (헤더 {total_headers}개 중 {len(index_list)}개): {index_list}")
        
        return index_list
    
    @staticmethod
    def _extract_row_headers(tr: Tag) -> List[str]:
        """
        단일 행에서 헤더 추출 (colspan 처리)
        
        Args:
            tr: tr 태그
        
        Returns:
            헤더 리스트
        """
        row_headers = []
        ths = tr.find_all("th", recursive=False)
        
        for col_idx, th in enumerate(ths):
            text = th.get_text(strip=True)
            if not text:
                continue
            
            # 첫 번째 th는 행 구분자로 스킵 (2개 이상일 때만)
            if col_idx == 0 and len(ths) > 1:
                continue
            
            # colspan 처리
            colspan = HeaderExtractor._get_colspan(th)
            row_headers.extend([text] * colspan)
        
        return row_headers
    
    @staticmethod
    def _get_colspan(th: Tag) -> int:
        """colspan 속성 추출"""
        colspan_attr = th.get("colspan")
        try:
            return int(colspan_attr) if colspan_attr else 1
        except ValueError:
            return 1


class BodyExtractor:
    """테이블 바디 추출 클래스"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.last_span_text: Optional[str] = None
    
    def extract(
        self,
        tbody: Tag,
        index_list: List[str]
    ) -> Dict[Tuple[str, str], List[str]]:
        """
        tbody에서 데이터 딕셔너리 추출
        
        Args:
            tbody: tbody 태그
            index_list: 헤더 인덱스 리스트
        
        Returns:
            {(카테고리, 항목): [값들]} 형태의 딕셔너리
        """
        data_dict = {}
        tbody_trs = tbody.find_all("tr", recursive=False)
        
        logger.info(f"발견된 행 수: {len(tbody_trs)}")
        
        if self.debug and tbody_trs:
            logger.debug(f"첫 행 HTML: {str(tbody_trs[0])[:500]}")
        
        processed_count = 0
        
        for idx, tr in enumerate(tbody_trs):
            self._log_progress(idx, len(tbody_trs))
            
            try:
                # 행 데이터 추출
                column_tuple, values = self._extract_row_data(tr, idx)
                
                if not column_tuple or not values:
                    continue
                
                # 헤더와 값 개수 검증
                if len(values) == len(index_list):
                    data_dict[column_tuple] = values
                    processed_count += 1
                    
                    if self.debug and idx < 3:
                        logger.debug(f"행 {idx} 성공!")
                else:
                    if self.debug and idx < 5:
                        logger.warning(
                            f"행 {idx} 길이 불일치: "
                            f"헤더={len(index_list)}, 값={len(values)} (스킵)"
                        )
            
            except Exception as e:
                if self.debug and idx < 5:
                    logger.error(f"행 {idx} 처리 중 에러: {e}")
                continue
        
        logger.info(f"처리 완료: {processed_count}/{len(tbody_trs)} 행")
        
        return data_dict
    
    def _extract_row_data(
        self,
        tr: Tag,
        idx: int
    ) -> Tuple[Optional[Tuple[str, str]], List[str]]:
        """
        단일 행에서 컬럼명과 값 추출
        
        Args:
            tr: tr 태그
            idx: 행 인덱스
        
        Returns:
            (컬럼명_튜플, 값_리스트)
        """
        # th 찾기
        th = tr.find("th")
        if not th:
            if self.debug and idx < 3:
                logger.debug(f"행 {idx}: th 없음")
            return None, []
        
        # 컬럼명 추출
        column_tuple = self._extract_column_name(th, idx)
        
        # td 값들 추출
        tds = tr.find_all("td", recursive=False)
        values = [td.get_text(strip=True) for td in tds]
        
        if self.debug and idx < 3:
            logger.debug(
                f"행 {idx}: column={column_tuple}, "
                f"td 개수={len(tds)}, 값={values[:3] if values else '없음'}"
            )
        
        return column_tuple, values
    
    def _extract_column_name(self, th: Tag, idx: int) -> Tuple[str, str]:
        """
        th에서 컬럼명 튜플 추출 (span 고려)
        
        Args:
            th: th 태그
            idx: 행 인덱스
        
        Returns:
            (카테고리, 항목) 튜플
        """
        span = th.find("span")
        th_text = th.get_text(strip=True)
        
        # span이 있는 경우: 새로운 상위 카테고리
        if span:
            span_text = span.get_text(strip=True)
            self.last_span_text = span_text
            column_tuple = (span_text, th_text)
            
            if self.debug and idx < 3:
                logger.debug(f"행 {idx} (span): {column_tuple}")
        
        # span 없는 경우: 이전 카테고리 사용
        else:
            if self.last_span_text:
                column_tuple = (self.last_span_text, th_text)
            else:
                column_tuple = (th_text, "")
            
            if self.debug and idx < 3:
                logger.debug(f"행 {idx} (no span): {column_tuple}")
        
        return column_tuple
    
    @staticmethod
    def _log_progress(idx: int, total: int):
        """
        진행상황 로깅 (20개마다)
        
        Args:
            idx (int): 로그 번호
            total (int): 로그 최대값
        """
        if idx > 0 and idx % 20 == 0:
            logger.info(f"처리 중: {idx}/{total} 행")
