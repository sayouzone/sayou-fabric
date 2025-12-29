
import logging
import re

from bs4 import BeautifulSoup, Tag
from typing import Dict, List, Optional, Tuple, Union

from ..models import HistoryData

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TableFinder:
    """테이블 검색 클래스"""
    
    @staticmethod
    def find_by_title(soup: BeautifulSoup, title: str) -> Optional[Tag]:
        """제목으로 테이블 찾기"""
        for table in soup.find_all("table"):
            if title in table.get_text():
                return table
        
        return None
    
    @staticmethod
    def find_by_ids(soup: BeautifulSoup, ids: list[str]) -> Optional[Tag]:
        """제목으로 테이블 찾기"""
        tables = {id: None for id in ids}
        for table in soup.find_all("div", id=lambda x: x in ids):
            tables[table.get("id")] = table
        
        return tables
    
    @staticmethod
    def find(soup: BeautifulSoup) -> List[Tag]:
        """제목으로 테이블 찾기"""
        tables = []
        for table in soup.find_all("table"):
            #print(table)
            tables.append(table)
        
        return tables

# =============================================================================
# 헤더 추출기
# =============================================================================

class HeaderExtractor:
    """테이블 헤더 추출 클래스"""

    # 기간 패턴 (YYYY/MM)
    PERIOD_PATTERN = re.compile(r"^\d{4}/\d{2}$")
    
    @staticmethod
    def extract_headers(thead: Tag) -> List[str]:
        """
        thead에서 인덱스 리스트 추출
        
        Args:
            thead: thead 태그
        
        Returns:
            인덱스 리스트 (날짜/기간 데이터)
        """
        thead_rows = thead.find_all("tr")
        header_rows: List[List[str]] = []
        
        # tr이 있는 경우
        for tr in thead_rows:
            row_headers = HeaderExtractor._extract_row_headers(tr)
            if row_headers:
                header_rows.append(row_headers)
        
        # tr이 없고 직접 th가 있는 경우 (예: <thead><th>...</th><th>...</th></thead>)
        if not header_rows:
            direct_ths = thead.find_all("th", recursive=False)
            if direct_ths:
                headers = []
                for idx, th in enumerate(direct_ths):
                    div = th.find("div")
                    text = div.get_text(strip=True) if div else th.get_text(strip=True)
                    if text:
                        # 첫 번째 th는 행 라벨일 수 있음
                        if idx == 0 and len(direct_ths) > 1:
                            continue
                        colspan = HeaderExtractor._get_colspan(th)
                        headers.extend([text] * colspan)
                if headers:
                    header_rows.append(headers)
        
        # 가장 긴 행을 선택 (가장 상세한 헤더)
        headers = max(header_rows, key=len) if header_rows else []
        
        total_ths = len(thead.find_all("th"))
        logger.info(f"기간 데이터 (헤더 {total_ths}개 중 {len(headers)}개): {headers}")
        
        return headers
    
    @classmethod
    def extract_from_first_row(cls, tbody: Tag) -> List[str]:
        """tbody 첫 번째 행에서 헤더 추출 (thead 없는 경우)"""
        first_tr = tbody.find("tr")
        if not first_tr:
            return []
        
        headers = []
        for th in first_tr.find_all("th"):
            text = th.get_text(strip=True)
            if text:
                colspan = cls._get_colspan(th)
                headers.extend([text] * colspan)
        
        return headers
    
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
            # div 안의 텍스트도 확인
            div = th.find("div")
            text = div.get_text(strip=True) if div else th.get_text(strip=True)
            if not text:
                continue
            
            # 첫 번째 th는 행 구분자로 스킵 (2개 이상일 때만)
            if col_idx == 0 and len(ths) > 1:
                continue

            # 기간 패턴인지 확인
            if not HeaderExtractor.PERIOD_PATTERN.match(text):
                continue
            
            # colspan 처리
            colspan = HeaderExtractor._get_colspan(th)
            row_headers.extend([text] * colspan)
        
        return row_headers
    
    @staticmethod
    def _get_colspan(tag: Tag) -> int:
        """colspan 속성 추출"""
        try:
            return int(tag.get("colspan", 1))
        except (ValueError, TypeError):
            return 1

# =============================================================================
# 바디 추출기
# =============================================================================

class BodyExtractor:
    """테이블 바디 추출 클래스"""
    
    # 스킵할 행 클래스 (세부 계정)
    SKIP_ROW_CLASSES = {"acd_dep2_sub", "c_grid_1"}
    
    # 카테고리 행 클래스
    CATEGORY_ROW_CLASS = "tbody_tit"
    
    def __init__(
        self, 
        include_hidden: bool = False,
        use_category: bool = False,
        debug: bool = False
    ):
        """
        Args:
            include_hidden: 숨겨진 행 포함 여부
            use_category: 카테고리 사용 여부
            debug: 디버그 로깅 활성화
        """
        self.include_hidden = include_hidden
        self.use_category = use_category
        self.debug = debug
        self.current_category: str = ""
    
    def extract(
        self,
        tbody: Tag,
        headers: List[str]
    ) -> Union[Dict[str, List[str]], Dict[Tuple[str, str], List[str]]]:
        """
        tbody에서 데이터 딕셔너리 추출
        
        Args:
            tbody: tbody 태그
            headers: 헤더 리스트
        
        Returns:
            {(카테고리, 항목): [값들]} 형태의 딕셔너리
        """
        data = {}
        rows = tbody.find_all("tr", recursive=False)
        
        logger.info(f"발견된 행 수: {len(rows)}")
        processed = 0
        
        for idx, tr in enumerate(rows):
            row_classes = set(tr.get("class", []))
            
            # 카테고리 행 처리
            if self.CATEGORY_ROW_CLASS in row_classes:
                self.current_category = self._extract_category(tr)
                logger.debug(f"카테고리: {self.current_category}")
                continue
            
            # 숨겨진 행 스킵
            if not self.include_hidden:
                if row_classes & self.SKIP_ROW_CLASSES:
                    continue
                # style="display:none" 체크
                style = tr.get("style", "")
                if "display:none" in style.replace(" ", ""):
                    continue
            
            # 행 데이터 추출
            key, values = self._extract_row(tr)
            
            if not key:
                continue
            
            # 값 개수 검증
            if len(values) != len(headers):
                if self.debug:
                    logger.warning(f"행 {idx} 길이 불일치: {len(values)} vs {len(headers)}")
                continue
            
            # 키 생성
            if self.use_category:
                full_key = (self.current_category, key)
            else:
                full_key = key
            
            data[full_key] = values
            processed += 1
        
        logger.info(f"처리 완료: {processed}/{len(rows)} 행")
        return data
    
    def _extract_category(self, tr: Tag) -> str:
        """카테고리 행에서 카테고리명 추출"""
        th = tr.find("th")
        return th.get_text(strip=True) if th else ""
    
    def _extract_row(self, tr: Tag) -> Tuple[str, List[str]]:
        """행에서 키와 값 추출"""
        # 키 추출 (th에서)
        th = tr.find("th")
        if th:
            key = self._extract_key(th)
        else:
            # th 없으면 첫 번째 td
            first_td = tr.find("td")
            key = first_td.get_text(strip=True) if first_td else ""
        
        # 값 추출 (td들)
        tds = tr.find_all("td", recursive=False)
        
        # th가 없으면 첫 번째 td는 키로 사용했으므로 제외
        if not tr.find("th") and tds:
            tds = tds[1:]
        
        values = [self._extract_cell_value(td) for td in tds]
        
        return key, values
    
    def _extract_key(self, th: Tag) -> str:
        """th에서 키 추출"""
        # txt_acd span 우선
        txt_acd = th.find("span", class_="txt_acd")
        if txt_acd:
            return txt_acd.get_text(strip=True)
        
        # div 내부 텍스트
        div = th.find("div")
        if div:
            return div.get_text(strip=True)
        
        return th.get_text(strip=True)
    
    def _extract_cell_value(self, td: Tag) -> str:
        """td에서 값 추출"""
        # title 속성 우선 (정밀 값)
        title = td.get("title")
        if title:
            return title.strip()
        
        # 링크 href 확인 (홈페이지 등)
        link = td.find("a")
        if link and link.get("href", "").startswith("javascript:goHompage"):
            return link.get_text(strip=True)
        
        return td.get_text(strip=True)

# =============================================================================
# 키-값 테이블 추출기 (General Information 등)
# =============================================================================

class KeyValueExtractor:
    """
    키-값 형태 테이블 추출기
    키-값 테이블 추출기 (General Information 등)
    """
    
    def extract(self, tbody: Tag) -> Dict[str, str]:
        """
        2열 또는 4열 키-값 테이블 추출
        
        Returns:
            {키: 값} 딕셔너리
        """
        data = {}
        
        for tr in tbody.find_all("tr", recursive=False):
            ths = tr.find_all("th", recursive=False)
            tds = tr.find_all("td", recursive=False)
            
            # th-td 쌍 추출
            pairs = self._extract_pairs(ths, tds)
            data.update(pairs)
        
        logger.info(f"키-값 추출: {len(data)}개")
        return data
    
    def _extract_pairs(
        self,
        ths: List[Tag],
        tds: List[Tag]
    ) -> Dict[str, str]:
        """th-td 쌍에서 키-값 추출"""
        pairs = {}
        
        # 일반적으로 th와 td가 번갈아 나옴
        # 또는 th 하나에 colspan된 td
        
        td_idx = 0
        for th in ths:
            key = self._get_text(th)
            if not key:
                continue
            
            # 대응하는 td 찾기
            if td_idx < len(tds):
                td = tds[td_idx]
                colspan = int(td.get("colspan", 1))
                value = self._get_text(td)
                pairs[key] = value
                td_idx += 1
                
                # colspan이 여러 개면 다음 th는 그만큼 건너뜀
                if colspan > 1:
                    td_idx += colspan - 1
        
        return pairs
    
    def _get_text(self, tag: Tag) -> str:
        """태그에서 텍스트 추출"""
        div = tag.find("div")
        if div:
            return div.get_text(strip=True)
        
        link = tag.find("a")
        if link:
            return link.get_text(strip=True)
        
        return tag.get_text(strip=True)

# =============================================================================
# 연혁 테이블 추출기
# =============================================================================

class HistoryExtractor:
    """연혁/이력 테이블 추출기"""
    
    def extract(self, table: Tag) -> HistoryData:
        """연혁 테이블 추출"""
        result = HistoryData()
        
        # Caption
        caption = table.find("caption")
        result.caption = caption.get_text(strip=True) if caption else ""
        
        # Headers
        thead = table.find("thead")
        if thead:
            result.headers = self._extract_headers(thead)
        
        # Records
        tbody = table.find("tbody")
        if tbody:
            result.records = self._extract_records(tbody, result.headers)
        
        return result
    
    def _extract_headers(self, thead: Tag) -> List[str]:
        """헤더 추출"""
        headers = []
        for th in thead.find_all("th"):
            text = th.get_text(strip=True)
            if text:
                headers.append(text)
        return headers
    
    def _extract_records(
        self,
        tbody: Tag,
        headers: List[str]
    ) -> List[Dict[str, str]]:
        """레코드 추출"""
        records = []
        
        for tr in tbody.find_all("tr", recursive=False):
            tds = tr.find_all("td", recursive=False)
            
            if len(tds) != len(headers):
                continue
            
            record = {}
            for header, td in zip(headers, tds):
                # title 속성 우선
                value = td.get("title") or td.get_text(strip=True)
                record[header] = value
            
            records.append(record)
        
        return records
