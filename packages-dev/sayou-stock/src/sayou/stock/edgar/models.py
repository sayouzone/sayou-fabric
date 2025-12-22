"""
SEC EDGAR 데이터 모델 정의
"""

from dataclasses import dataclass, field
from typing import Optional


# ============================================================
# 공통 모델
# ============================================================

@dataclass
class CompanyInfo:
    """회사 기본 정보"""
    cik: str
    name: str
    ticker: Optional[str] = None
    sic: Optional[str] = None
    industry: Optional[str] = None


@dataclass
class FilingMetadata:
    """파일링 메타데이터"""
    accession_number: str
    filing_type: str
    filing_date: str
    period_of_report: Optional[str] = None
    document_url: str = ""


# ============================================================
# 10-K / 10-Q 관련 모델
# ============================================================

@dataclass
class FinancialData:
    """재무 데이터"""
    revenue: Optional[float] = None
    net_income: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    stockholders_equity: Optional[float] = None
    eps_basic: Optional[float] = None
    eps_diluted: Optional[float] = None
    operating_income: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    
    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


# ============================================================
# 8-K 관련 모델
# ============================================================

@dataclass
class Filing8KData:
    """8-K 이벤트 데이터"""
    items: list = field(default_factory=list)
    event_descriptions: list = field(default_factory=list)


# ============================================================
# 13F 관련 모델
# ============================================================

@dataclass
class Holding13F:
    """13F 개별 보유 종목"""
    issuer_name: str
    title_of_class: str
    cusip: str
    value: float  # USD (thousands)
    shares_or_principal: float
    shares_or_principal_type: str  # SH (shares) or PRN (principal)
    investment_discretion: str  # SOLE, SHARED, NONE
    voting_authority_sole: int = 0
    voting_authority_shared: int = 0
    voting_authority_none: int = 0
    put_call: Optional[str] = None  # PUT, CALL, or None


@dataclass
class Filing13FData:
    """13F 파일링 전체 데이터"""
    filer_name: str = ""
    filer_cik: str = ""
    report_period: str = ""
    filing_date: str = ""
    total_value: float = 0.0
    holdings_count: int = 0
    holdings: list = field(default_factory=list)
    top_holdings: list = field(default_factory=list)
    sector_allocation: dict = field(default_factory=dict)


# ============================================================
# DEF 14A 관련 모델
# ============================================================

@dataclass
class ExecutiveCompensation:
    """임원 보상 정보"""
    name: str
    title: str = ""
    year: int = 0
    salary: float = 0.0
    bonus: float = 0.0
    stock_awards: float = 0.0
    option_awards: float = 0.0
    non_equity_incentive: float = 0.0
    pension_change: float = 0.0
    other_compensation: float = 0.0
    total: float = 0.0
    
    def calculate_total(self) -> float:
        """총 보상 계산"""
        return (
            self.salary + self.bonus + self.stock_awards + 
            self.option_awards + self.non_equity_incentive + 
            self.pension_change + self.other_compensation
        )


@dataclass
class DirectorInfo:
    """임원 정보"""
    name: str
    age: Optional[int] = None
    position: str = ""
    committees: list = field(default_factory=list)
    independent: bool = False
    tenure_years: Optional[int] = None
    other_boards: list = field(default_factory=list)
    shares_owned: int = 0
    compensation: float = 0.0


@dataclass 
class ShareholderProposal:
    """주주 제안"""
    proposal_number: int
    title: str
    proponent: str = ""
    description: str = ""
    board_recommendation: str = ""
    vote_required: str = ""
    prior_year_support: Optional[float] = None


@dataclass
class OwnershipInfo:
    """주요 주주 정보"""
    name: str
    shares: int = 0
    percentage: float = 0.0
    is_insider: bool = False
    is_institution: bool = False


@dataclass
class DEF14AData:
    """DEF 14A Proxy Statement 전체 데이터"""
    company_name: str = ""
    cik: str = ""
    filing_date: str = ""
    meeting_date: str = ""
    meeting_type: str = ""
    record_date: str = ""
    
    # 임원 보상
    executive_compensation: list = field(default_factory=list)
    ceo_pay_ratio: Optional[float] = None
    ceo_name: str = ""
    median_employee_pay: Optional[float] = None
    
    # 이사회
    directors: list = field(default_factory=list)
    board_size: int = 0
    independent_directors: int = 0
    board_diversity: dict = field(default_factory=dict)
    
    # 주주 제안
    proposals: list = field(default_factory=list)
    
    # 주요 주주
    major_shareholders: list = field(default_factory=list)
    insider_ownership_pct: float = 0.0
    institutional_ownership_pct: float = 0.0
    
    # 거버넌스
    governance_highlights: list = field(default_factory=list)
    related_party_transactions: list = field(default_factory=list)
    say_on_pay_vote: str = ""
    prior_say_on_pay_support: Optional[float] = None
