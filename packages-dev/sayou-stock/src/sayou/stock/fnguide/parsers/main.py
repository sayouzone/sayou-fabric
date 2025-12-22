import pandas as pd
import requests

from io import StringIO
from typing import Dict, List, Tuple, Optional, Any

from ..client import FnGuideClient

from ..utils import (
    urls,
)

class FnGuideMainParser:
    """
    FnGuide Main(Snapshot) 파싱 클래스
    한글 컬럼명을 영문으로 번역하는 헬퍼 클래스

    테이블의 한글 헤더를 미리 정의된 영문 이름으로 변환하여
    데이터 분석 시 일관성 있는 컬럼명 사용 가능
    
    Snapshot, https://comp.fnguide.com/SVO2/ASP/SVD_main.asp?gicode=A{stock}
    """

    # 정적 HTML에서 가져올 테이블 (원본 utils/fnguide.py)
    _main_table_selectors = [
        ("market_conditions", 0),
        ("earning_issue", 1),
        ("holdings_status", 2),
        ("governance", 3),
        ("shareholders", 4),
        ("bond_rating", 6),
        ("analysis", 7),
        ("industry_comparison", 8),
        ("financialhighlight_annual", 11),
        ("financialhighlight_netquarter", 12),
    ]

    # 한글 → 영문 컬럼명 매핑 딕셔너리
    _COLUMN_MAP = {
        "잠정실적발표예정일": "tentative_results_announcement_date",
        "예상실적(영업이익, 억원)": "expected_operating_profit_billion_krw",
        "3개월전예상실적대비(%)": "expected_operating_profit_vs_3m_pct",
        "전년동기대비(%)": "year_over_year_pct",
        "운용사명": "asset_manager_name",
        "보유수량": "shares_held",
        "시가평가액": "market_value_krw",
        "상장주식수내비중": "share_of_outstanding_shares_pct",
        "운용사내비중": "manager_portfolio_ratio_pct",
        "항목": "item",
        "보통주": "common_shares",
        "지분율": "ownership_ratio_pct",
        "최종변동일": "last_change_date",
        "주주구분": "shareholder_category",
        "대표주주수": "major_shareholder_count",
        "투자의견": "investment_opinion",
        "목표주가": "target_price",
        "추정기관수": "estimate_institution_count",
        "구분": "category",
        "코스피 전기·전자": "kospi_electronics",
        "헤더": "header",
        "헤더.1": "header_1",
        "IFRS(연결)": "ifrs_consolidated",
        "IFRS(별도)": "ifrs_individual",
    }

    def __init__(self, client: FnGuideClient):
        self.client = client
    
    def parse(self, stock: str):
        """
        기업 정보 | Snapshot 정보 추출 후 주요 키를 영어로 변환
        requests로 HTML을 가져온 후 pandas.read_html()로 파싱

        Args:
            html_text (str): HTML text
            stock: 종목 코드 (회사명을 "company"로 치환하기 위해 사용)

        Returns:
            Dict: 컬럼명이 번역된 DataFrame
        """

        url = urls.get("메인")

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

        frames = pd.read_html(StringIO(response.text))

        datasets = {}
        stock = stock if stock else self.stock
        
        for name, index in self._main_table_selectors:
            if index < len(frames):
                frame = frames[index]
                
                # 한글 컬럼명을 영문으로 번역
                frame = self._translate(
                    frame,
                    stock=stock,
                )
                datasets[name] = frame.to_dict(orient="records")
            else:
                logger.error(f"경고: '{name}'에 해당하는 테이블(index {index})을 찾지 못해 빈 데이터로 저장합니다.")
                datasets[name] = []

        return datasets

    def _translate(
        self,
        frame: pd.DataFrame,
        stock: str | None = None,
    ) -> pd.DataFrame:
        """
        DataFrame의 한글 컬럼명을 영문으로 번역

        단일 인덱스와 멀티 인덱스 모두 지원

        Args:
            frame: 번역할 DataFrame
            stock: 종목 코드 (회사명을 "company"로 치환하기 위해 사용)

        Returns:
            pd.DataFrame: 컬럼명이 번역된 DataFrame
        """
        if frame.empty:
            return frame

        # 종목 코드로부터 회사명 조회
        company_name = None
        if stock:
            try:
                from utils.companydict import companydict
                company_name = companydict.get_company_by_code(stock)
                if company_name:
                    company_name = self._normalize(company_name)
            except (ImportError, ModuleNotFoundError):
                try:
                    from ..companydict import companydict
                    company_name = companydict.get_company_by_code(stock)
                    if company_name:
                        company_name = self._normalize(company_name)
                except (ImportError, ModuleNotFoundError):
                    pass

        translated = frame.copy()

        # 멀티인덱스 처리
        if isinstance(translated.columns, pd.MultiIndex):
            new_columns = []
            for column in translated.columns:
                # 각 레벨별로 번역
                new_columns.append(
                    tuple(self._translate_token(level, company_name) for level in column)
                )
            translated.columns = pd.MultiIndex.from_tuples(
                new_columns, names=translated.columns.names
            )
        # 단일 인덱스 처리
        else:
            translated.rename(
                columns=lambda label: self._translate_token(label, company_name),
                inplace=True,
            )

        return translated

    def _translate_token(self, label: str, company_name: str | None) -> str:
        """
        개별 컬럼명 토큰 번역

        Args:
            label: 원본 컬럼명
            company_name: 회사명 (해당 컬럼을 "company"로 치환)

        Returns:
            str: 번역된 컬럼명
        """
        if not isinstance(label, str):
            return label

        normalized = self._normalize(label)

        # 회사명이면 "company"로 통일
        if company_name and normalized == company_name:
            return "company"

        # 매핑 딕셔너리에서 찾기 (없으면 원본 그대로)
        return self._COLUMN_MAP.get(normalized, normalized)

    @property
    @staticmethod
    def main_table_selectors(self) -> List[Tuple[str, int]]:
        """
        Snapshot HTML에서 가져올 테이블 선택자

        Returns:
            List[Tuple[str, int]]: (테이블명, 인덱스) 튜플 리스트
        """
        return self._main_table_selectors

    @staticmethod
    def _normalize(value: str) -> str:
        """
        문자열 정규화 (공백 문자 제거 및 trim)

        Args:
            value: 원본 문자열

        Returns:
            str: 정규화된 문자열
        """
        return value.replace("\xa0", " ").strip()