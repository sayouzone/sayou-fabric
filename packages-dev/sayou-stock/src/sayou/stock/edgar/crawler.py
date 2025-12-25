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
 
"""
SEC EDGAR Crawler - 통합 인터페이스
"""

import logging
import re
from typing import Optional

from .client import EDGARClient
from .models import (
    FilingMetadata,
    FinancialData,
    Filing8KData,
    Filing13FData,
    DEF14AData,
)
from .parsers import (
    Form10KParser,
    Form10QParser,
    Form8KParser,
    Form13FParser,
    DEF14AParser,
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EDGARCrawler:
    """
    SEC EDGAR 파일링 추출기 (통합 인터페이스)
    
    지원 파일링:
        - 10-K: 연간 보고서
        - 10-Q: 분기 보고서
        - 8-K: 중요 이벤트 공시
        - 13F: 기관투자자 포트폴리오
        - DEF 14A: Proxy Statement (위임장 설명서)
    
    Example:
        >>> crawler = EDGARCrawler(user_agent="Sayouzone sjkim@sayouzone.com")
        >>> cik = crawler.fetch_cik_by_ticker("AAPL")
        >>> filings = crawler.fetch_filings(cik, doc_type="10-K", count=1)
        >>> data = crawler.extract_10k(cik, filings[0].document_url, filings[0].accession_number)
    """
    
    def __init__(self, user_agent: str = "Sayouzone sjkim@sayouzone.com"):
        """
        Args:
            user_agent: SEC에서 요구하는 User-Agent (회사명 + 이메일)
        """
        self.client = EDGARClient(user_agent)
        
        # 파서 초기화
        self._10k_parser = Form10KParser(self.client)
        self._10q_parser = Form10QParser(self.client)
        self._8k_parser = Form8KParser(self.client)
        self._13f_parser = Form13FParser(self.client)
        self._def14a_parser = DEF14AParser(self.client)
    
    # ============================================================
    # 공통 메서드
    # ============================================================
    
    def fetch_cik_by_ticker(self, ticker: str) -> Optional[str]:
        """티커 심볼로 CIK 번호 조회"""
        return self.client.fetch_cik_by_ticker(ticker)
    
    def fetch_cik_by_company(self, company: str, limit: int = 10, flags: int = re.IGNORECASE) -> list[dict]:
        """정규표현식으로 회사명 검색"""
        return self.client.fetch_cik_by_company(company, limit, flags)
    
    def search_filings(
        self,
        query: str,
        filing_types: list[str] = None,
        start_date: str = None,
        end_date: str = None,
        size: int = 10
    ) -> list[dict]:
        """EDGAR 전문 검색"""
        return self.client.search_filings(
            query, filing_types, start_date, end_date, size
        )
    
    def fetch_filings(
        self, cik: str, 
        doc_type: str = "10-K", 
        count: int = 10
    ) -> list[FilingMetadata]:
        """10-K, 10-Q, 8-K, 13F, DEF 14A 파일링 목록 조회"""

        if doc_type == '10-Q':
            return self._10q_parser.fetch_filings(cik, count)
        elif doc_type == '8-K':
            return self._8k_parser.fetch_filings(cik, count)
        elif doc_type == '13F':
            return self._13f_parser.fetch_filings(cik, count)
        elif doc_type == 'DEF 14A':
            return self._def14a_parser.fetch_filings(cik, count)
        
        return self._10k_parser.fetch_filings(cik, count)
    
    # ============================================================
    # 10-K 메서드
    # ============================================================
    
    def fetch_10k_filings(self, cik: str, count: int = 10) -> list[FilingMetadata]:
        """10-K 파일링 목록 조회"""
        return self._10k_parser.fetch_filings(cik, count)
    
    def extract_10k(self, cik: str, filing_url: str, accession_number: str) -> dict:
        """
        10-K에서 데이터 추출
        
        Returns:
            dict: {
                "sections": dict,       # Item 1, 1A, 7 등 섹션별 텍스트
                "financial_data": FinancialData,  # XBRL 재무 데이터
                "risk_factors": list,   # 리스크 팩터 목록
                "business_description": str
            }
        """
        return self._10k_parser.extract(cik, filing_url, accession_number)
    
    # ============================================================
    # 10-Q 메서드
    # ============================================================
    
    def fetch_10q_filings(self, cik: str, count: int = 10) -> list[FilingMetadata]:
        """10-Q 파일링 목록 조회"""
        return self._10q_parser.fetch_filings(cik, count)
    
    def extract_10q(self, cik: str, filing_url: str, accession_number: str) -> dict:
        """
        10-Q에서 데이터 추출
        
        Returns:
            dict: {
                "sections": dict,
                "financial_data": FinancialData,
                "md_and_a": str  # Management Discussion & Analysis
            }
        """
        return self._10q_parser.extract(cik, filing_url, accession_number)
    
    # ============================================================
    # 8-K 메서드
    # ============================================================
    
    def fetch_8k_filings(self, cik: str, count: int = 10) -> list[FilingMetadata]:
        """8-K 파일링 목록 조회"""
        return self._8k_parser.fetch_filings(cik, count)
    
    def extract_8k(self, cik: str, filing_url: str, accession_number: str) -> Filing8KData:
        """
        8-K에서 이벤트 데이터 추출
        
        Returns:
            Filing8KData: {
                items: list,             # 보고된 아이템 코드
                event_descriptions: list # 각 아이템별 설명
            }
        """
        return self._8k_parser.extract(cik, filing_url, accession_number)
    
    # ============================================================
    # 13F 메서드
    # ============================================================
    
    def fetch_13f_filings(self, cik: str, count: int = 10) -> list[FilingMetadata]:
        """13F 파일링 목록 조회"""
        return self._13f_parser.fetch_filings(cik, count)
    
    def extract_13f(self, cik: str, filing_url: str, accession_number: str) -> Filing13FData:
        """
        13F에서 포트폴리오 데이터 추출
        
        Returns:
            Filing13FData: {
                holdings: list,      # 전체 보유 종목
                top_holdings: list,  # 상위 10개 종목
                total_value: float,  # 총 운용자산 (천 달러)
                holdings_count: int
            }
        """
        return self._13f_parser.extract(cik, filing_url, accession_number)
    
    def compare_13f(
        self, 
        cik: str, 
        filing_url_current: str,
        filing_url_previous: str,
        accession_current: str, 
        accession_previous: str
    ) -> dict:
        """
        두 분기의 13F 비교 (포트폴리오 변화 분석)
        
        Returns:
            dict: {
                new_positions: list,       # 신규 매수
                closed_positions: list,    # 완전 매도
                increased_positions: list, # 비중 확대
                decreased_positions: list  # 비중 축소
            }
        """
        return self._13f_parser.compare(cik, filing_url_current, filing_url_previous, accession_current, accession_previous)
    
    # ============================================================
    # DEF 14A 메서드
    # ============================================================
    
    def fetch_def14a_filings(self, cik: str, count: int = 10) -> list[FilingMetadata]:
        """DEF 14A 파일링 목록 조회"""
        return self._def14a_parser.fetch_filings(cik, count)
    
    def extract_def14a(self, cik: str, filing_url: str, accession_number: str) -> DEF14AData:
        """
        DEF 14A에서 프록시 데이터 추출
        
        Returns:
            DEF14AData: {
                executive_compensation: list,  # 임원 보상
                directors: list,               # 이사 정보
                proposals: list,               # 투표 안건
                major_shareholders: list,      # 주요 주주
                ceo_pay_ratio: float,
                governance_highlights: list
            }
        """
        return self._def14a_parser.extract(cik, filing_url, accession_number)
    
    def analyze_compensation_trends(self, cik: str, years: int = 3) -> dict:
        """여러 연도의 임원 보상 트렌드 분석"""
        return self._def14a_parser.analyze_compensation_trends(cik, years)
    
    def compare_peer_compensation(self, ciks: list[str]) -> list[dict]:
        """동종 업계 임원 보상 비교"""
        return self._def14a_parser.compare_peers(ciks)
    
    # ============================================================
    # 레거시 호환 메서드 (기존 API 유지)
    # ============================================================
    
    def fetch_company_filings(
        self, 
        cik: str, 
        filing_type: str = "10-K", 
        count: int = 10
    ) -> list[FilingMetadata]:
        """회사의 파일링 목록 조회 (레거시 호환)"""
        return self.client.fetch_company_filings(cik, filing_type, count)
    
    def extract_10k_data(self, cik: str, accession_number: str) -> dict:
        """10-K 데이터 추출 (레거시 호환)"""
        return self.extract_10k(cik, accession_number)
    
    def extract_10q_data(self, cik: str, accession_number: str) -> dict:
        """10-Q 데이터 추출 (레거시 호환)"""
        return self.extract_10q(cik, accession_number)
    
    def extract_8k_data(self, cik: str, accession_number: str) -> Filing8KData:
        """8-K 데이터 추출 (레거시 호환)"""
        return self.extract_8k(cik, accession_number)
    
    def extract_13f_data(self, cik: str, accession_number: str) -> Filing13FData:
        """13F 데이터 추출 (레거시 호환)"""
        return self.extract_13f(cik, accession_number)
    
    def extract_def14a_data(self, cik: str, accession_number: str) -> DEF14AData:
        """DEF 14A 데이터 추출 (레거시 호환)"""
        return self.extract_def14a(cik, accession_number)
    
    def compare_13f_filings(
        self, 
        cik: str, 
        accession_current: str, 
        accession_previous: str
    ) -> dict:
        """13F 비교 (레거시 호환)"""
        return self.compare_13f(cik, accession_current, accession_previous)
    
    def analyze_executive_compensation_trends(self, cik: str, years: int = 3) -> dict:
        """임원 보상 트렌드 (레거시 호환)"""
        return self.analyze_compensation_trends(cik, years)
