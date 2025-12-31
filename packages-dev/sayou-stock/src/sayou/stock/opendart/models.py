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
 
import os
from dataclasses import dataclass, field, asdict, fields
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional

@dataclass(frozen=True)
class DartConfig:
    """DART 크롤러 설정."""
    
    bucket_name: str
    api_key: str
    
    @classmethod
    def from_env(cls) -> "DartConfig":
        """환경 변수에서 설정을 로드합니다."""

        load_dotenv()

        bucket_name = "sayouzone-ai-stocks"
        api_key = os.environ.get("DART_API_KEY", "")
        #api_key = "fd664865257f1a3073b654f9185de11a708f726c"
        
        if not api_key:
            raise ValueError("DART_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        return cls(bucket_name=bucket_name, api_key=api_key)

class CorpClass(Enum):
    """법인 구분"""
    KOSPI = "Y"      # 유가증권시장
    KOSDAQ = "K"     # 코스닥
    KONEX = "N"      # 코넥스
    ETC = "E"        # 기타

    @classmethod
    def from_value(cls, value: Optional[str]) -> Optional["CorpClass"]:
        """값으로부터 Enum 생성"""
        if not value:
            return None
        for member in cls:
            if member.value == value:
                return member
        return None

    @property
    def display_name(self) -> str:
        """표시명"""
        names = {
            "Y": "유가증권",
            "K": "코스닥",
            "N": "코넥스",
            "E": "기타",
        }
        return names.get(self.value, "알 수 없음")

@dataclass
class DisclosureData:
    """
    공시정보 데이터 모델
    """
    
    corp_cls: Optional[CorpClass] = None # 법인구분 : Y(유가), K(코스닥), N(코넥스), E(기타)
    corp_code: Optional[str] = None # 고유번호
    corp_name: Optional[str] = None # 종목명(법인명)
    corp_name_eng: Optional[str] = None # 영문명칭
    corp_eng_name: Optional[str] = None # 영문 정식명칭
    stock_name: Optional[str] = None # 종목명(상장사) 또는 약식명칭(기타법인)
    stock_code: Optional[str] = None # 상장회사인 경우 주식의 종목코드
    report_nm: Optional[str] = None # 보고서명
    rcept_no: Optional[str] = None # 접수번호
    flr_nm: Optional[str] = None # 공시 제출인명
    rm: Optional[str] = None # 비고
    ceo_nm: Optional[str] = None # 대표자명
    jurir_no: Optional[str] = None # 법인등록번호
    bizr_no: Optional[str] = None # 사업자등록번호
    adres: Optional[str] = None # 주소
    hm_url: Optional[str] = None # 홈페이지
    ir_url: Optional[str] = None # IR홈페이지
    phn_no: Optional[str] = None # 전화번호
    fax_no: Optional[str] = None # 팩스번호
    induty_code: Optional[str] = None # 업종코드
    acc_mt: Optional[str] = None # 결산월(MM)
    est_dt: Optional[str] = None # 설립일(YYYYMMDD)
    rcept_dt: Optional[str] = None # 접수일자
    modify_date: Optional[str] = None # 최종변경일자

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "DisclosureData":
        """API 응답에서 생성"""
        valid_fields = {f.name for f in fields(cls)}
        converted = {}
        for api_field, model_field in cls.FIELD_MAPPING.items():
            if api_field in raw_data and model_field in valid_fields:
                converted[model_field] = raw_data[api_field]
        return cls(**converted)

    @property
    def corp_class_enum(self) -> Optional[CorpClass]:
        """법인구분 Enum"""
        return CorpClass.from_value(self.corp_cls)

@dataclass
class BaseReportData:
    """보고서 데이터 베이스 클래스"""

    # 서브클래스에서 오버라이드
    FIELD_MAPPING: ClassVar[Dict[str, str]] = {}

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "BaseReportData":
        """API 응답에서 모델 생성"""
        valid_fields = {f.name for f in fields(cls)}
        converted = {}

        # 매핑된 필드 변환
        for api_field, model_field in cls.FIELD_MAPPING.items():
            if api_field in raw_data and model_field in valid_fields:
                converted[model_field] = raw_data[api_field]

        # 매핑에 없지만 필드명이 동일한 경우 직접 매핑
        for key, value in raw_data.items():
            if key in valid_fields and key not in converted:
                converted[key] = value

        return cls(**converted)

@dataclass
class BaseReportData:
    """보고서 데이터 베이스 클래스"""
    rcept_no: Optional[str] = None # 접수번호
    corp_code: Optional[str] = None # 고유번호
    corp_cls: Optional[CorpClass] = None # 법인구분
    corp_name: Optional[str] = None # 법인명

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

    @property
    def corp_class_enum(self) -> Optional[CorpClass]:
        """법인구분 Enum"""
        return CorpClass.from_value(self.corp_cls)

@dataclass
class StockIssuanceData(BaseReportData):
    """주식발행 현황 데이터 모델"""

    isu_dcrs_de: Optional[str] = None # 주식발행 감소일자
    isu_dcrs_stle: Optional[str] = None # 발행 감소 형태
    isu_dcrs_stock_knd: Optional[str] = None # 발행 감소 주식 종류
    isu_dcrs_qy: Optional[str] = None # 발행 감소 수량
    isu_dcrs_mstvdv_fval_amount: Optional[str] = None # 발행 감소 주당 액면 가액
    isu_dcrs_mstvdv_amount: Optional[str] = None # 발행 감소 주당 가액
    stlm_dt: Optional[str] = None # 결산기준일

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "StockIssuanceData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class DividendsData(BaseReportData):
    """배당에 관한 사항 데이터 모델"""

    se: Optional[str] = None # 구분
    stock_knd: Optional[str] = None # 주식 종류
    thstrm: Optional[int] = None # 당기
    frmtrm: Optional[int] = None # 전기
    lwfr: Optional[int] = None # 전전기
    stlm_dt: Optional[str] = None # 결산기준일

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "DividendsData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)


@dataclass
class TreasuryStockData(BaseReportData):
    """자기주식 취득 및 처분 현황 데이터 모델"""

    acqs_mth1: Optional[str] = None # 취득방법 대분류
    acqs_mth2: Optional[str] = None # 취득방법 중분류
    acqs_mth3: Optional[str] = None # 취득방법 소분류
    stock_knd: Optional[str] = None # 주식 종류
    bsis_qy: Optional[int] = None # 기초 수량
    change_qy_acqs: Optional[int] = None # 변동 수량 취득
    change_qy_dsps: Optional[int] = None # 변동 수량 처분
    change_qy_incnr: Optional[int] = None # 변동 수량 소각
    trmend_qy: Optional[int] = None # 기말 수량
    rm: Optional[str] = None # 비고
    stlm_dt: Optional[str] = None # 결산기준일

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "TreasuryStockData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class MajorShareholderData(BaseReportData):
    """주요주주 현황 데이터 모델"""

    nm: Optional[str] = None # 성명
    relate: Optional[str] = None # 관계
    stock_knd: Optional[str] = None # 주식 종류
    bsis_posesn_stock_co: Optional[int] = None # 기초 소유 주식 수
    bsis_posesn_stock_qota_rt: Optional[float] = None # 기초 소유 주식 지분율
    trmend_posesn_stock_co: Optional[int] = None # 기말 소유 주식 수
    trmend_posesn_stock_qota_rt: Optional[float] = None # 기말 소유 주식 지분율
    rm: Optional[str] = None # 비고
    stlm_dt: Optional[str] = None # 결산기준일

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "MajorShareholderData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class MajorShareholderChangeData(BaseReportData):
    """주요주주 변동현황 데이터 모델"""

    change_on: Optional[str] = None # 변동 일
    mxmm_shrholdr_nm: Optional[str] = None # 최대 주주 명
    posesn_stock_co: Optional[int] = None # 소유 주식 수
    qota_rt: Optional[float] = None # 지분율
    change_cause: Optional[str] = None # 변동 원인
    rm: Optional[str] = None # 비고
    stlm_dt: Optional[str] = None # 결산기준일

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "MajorShareholderChangeData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class MinorShareholderData(BaseReportData):
    """소액주주 현황 데이터 모델"""

    se: Optional[str] = None # 구분
    shrholdr_co: Optional[int] = None # 주주수
    shrholdr_tot_co: Optional[int] = None # 전체 주주수
    shrholdr_rate: Optional[float] = None # 주주 비율
    hold_stock_co: Optional[int] = None # 보유 주식수
    stock_tot_co: Optional[int] = None # 총발행 주식수
    hold_stock_rate: Optional[float] = None # 보유 주식 비율
    stlm_dt: Optional[str] = None # 결산기준일

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "MinorShareholderData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class ExecutiveData(BaseReportData):
    """임원 현황 데이터 모델"""

    nm: Optional[str] = None # 성명
    sexdstn: Optional[str] = None # 성별
    birth_ym: Optional[str] = None # 출생 년월
    ofcps: Optional[str] = None # 직위
    rgist_exctv_at: Optional[str] = None # 등기 임원 여부
    fte_at: Optional[str] = None # 상근 여부
    chrg_job: Optional[str] = None # 담당 업무
    main_career: Optional[str] = None # 주요 경력
    mxmm_shrholdr_relate: Optional[str] = None # 최대 주주 관계
    hffc_pd: Optional[str] = None # 재직 기간
    tenure_end_on: Optional[str] = None # 임기 만료 일
    stlm_dt: Optional[str] = None # 결산기준일
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "ExecutiveData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class EmployeeData(BaseReportData):
    """직원 현황 데이터 모델"""

    fo_bbm: Optional[str] = None # 사 업부문
    sexdstn: Optional[str] = None # 성별
    reform_bfe_emp_co_rgllbr: Optional[int] = None # 개정 전 직원 수 정규직
    reform_bfe_emp_co_cnttk: Optional[int] = None # 개정 전 직원 수 계약직
    reform_bfe_emp_co_etc: Optional[int] = None # 개정 전 직원 수 기타
    rgllbr_co: Optional[int] = None # 정규직 수
    rgllbr_abacpt_labrr_co: Optional[int] = None # 정규직 단시간 근로자 수
    cnttk_co: Optional[int] = None # 계약직 수
    cnttk_abacpt_labrr_co: Optional[int] = None # 계약직 단시간 근로자 수
    sm: Optional[int] = None # 합계
    avrg_cnwk_sdytrn: Optional[int] = None # 평균 근속 연수
    fyer_salary_totamt: Optional[int] = None # 연간 급여 총액
    jan_salary_am: Optional[int] = None # 1인평균 급여 액
    rm: Optional[str] = None # 비고
    stlm_dt: Optional[str] = None # 결산기준일
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "EmployeeData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class DirectorCompensationData(BaseReportData):
    """이사·감사의 개인별 보수현황(5억원 이상) 데이터 모델"""

    nm: Optional[str] = None # 이름
    ofcps: Optional[str] = None # 직위
    mendng_totamt: Optional[int] = None # 보수 총액
    mendng_totamt_ct_incls_mendng: Optional[int] = None # 보수 총액 비 포함 보수
    stlm_dt: Optional[str] = None # 결산기준일
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "DirectorCompensationData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class TotalDirectorCompensationData(BaseReportData):
    """이사·감사 전체의 보수현황(보수지급금액 - 이사·감사 전체) 데이터 모델"""

    nmpr: Optional[int] = None # 인원수
    mendng_totamt: Optional[int] = None # 보수 총액
    jan_avrg_mendng_am: Optional[int] = None # 1인 평균 보수 액
    rm: Optional[str] = None # 비고
    stlm_dt: Optional[str] = None # 결산기준일
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "TotalDirectorCompensationData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)


@dataclass
class IntercorporateInvestmentData(BaseReportData):
    """타법인 출자현황 데이터 모델"""

    inv_prm: Optional[str] = None # 법인명
    frst_acqs_de: Optional[str] = None # 최초 취득 일자
    invstmnt_purps: Optional[str] = None # 출자 목적
    frst_acqs_amount: Optional[int] = None # 최초 취득 금액
    bsis_blce_qy: Optional[int] = None # 기초 잔액 수량
    bsis_blce_qota_rt: Optional[float] = None # 기초 잔액 지분율
    bsis_blce_acntbk_amount: Optional[int] = None # 기초 잔액 장부 가액
    incrs_dcrs_acqs_dsps_qy: Optional[int] = None # 증가 감소 취득 처분 수량
    incrs_dcrs_acqs_dsps_amount: Optional[int] = None # 증가 감소 취득 처분 금액
    incrs_dcrs_evl_lstmn: Optional[int] = None # 증가 감소 평가 손액
    trmend_blce_qy: Optional[int] = None # 기말 잔액 수량
    trmend_blce_qota_rt: Optional[float] = None # 기말 잔액 지분율
    trmend_blce_acntbk_amount: Optional[int] = None # 기말 잔액 장부 가액
    recent_bsns_year_fnnr_sttus_tot_assets: Optional[int] = None # 최근 사업 연도 재무 현황 총 자산
    recent_bsns_year_fnnr_sttus_thstrm_ntpf: Optional[int] = None # 최근 사업 연도 재무 현황 당기 순이익
    stlm_dt: Optional[str] = None # 결산기준일
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "IntercorporateInvestmentData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class OutstandingSharesData(BaseReportData):
    """주식의 총수 현황 데이터 모델"""

    se: Optional[str] = None # 구분(증권의종류, 합계, 비고)
    isu_stock_totqy: Optional[int] = None # 발행할 주식의 총수
    now_to_isu_stock_totqy: Optional[int] = None # 현재까지 발행한 주식의 총수
    now_to_dcrs_stock_totqy: Optional[int] = None # 현재까지 감소한 주식의 총수
    redc: Optional[int] = None # 감자
    profit_incnr: Optional[int] = None # 이익소각
    rdmstk_repy: Optional[int] = None # 상환주식의 상환
    etc: Optional[int] = None # 기타
    istc_totqy: Optional[int] = None # 발행주식의 총수
    tesstk_co: Optional[int] = None # 자기주식수
    distb_stock_co: Optional[int] = None # 유통주식수
    stlm_dt: Optional[str] = None # 결산기준일
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "OutstandingSharesData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class DebtSecuritiesIssuanceData(BaseReportData):
    """채무증권 발행실적 데이터 모델"""

    isu_cmpny: Optional[str] = None # 발행회사
    scrits_knd_nm: Optional[str] = None # 증권종류
    isu_mth_nm: Optional[str] = None # 발행방법
    isu_de: Optional[str] = None # 발행일자
    facvalu_totamt: Optional[int] = None # 권면(전자등록)총액
    intrt: Optional[float] = None # 이자율
    evl_grad_instt: Optional[str] = None # 평가등급(평가기관)
    mtd: Optional[str] = None # 만기일
    repy_at: Optional[str] = None # 상환여부
    mngt_cmpny: Optional[str] = None # 주관회사
    stlm_dt: Optional[str] = None # 결산기준일
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "DebtSecuritiesIssuanceData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class CPOutstandingData(BaseReportData):
    """기업어음증권 미상환 잔액 데이터 모델"""

    remndr_exprtn1: Optional[int] = None # 잔여만기
    remndr_exprtn2: Optional[int] = None # 잔여만기
    de10_below: Optional[int] = None # 10일 이하
    de10_excess_de30_below: Optional[int] = None # 10일초과 30일이하
    de30_excess_de90_below: Optional[int] = None # 30일초과 90일이하
    de90_excess_de180_below: Optional[int] = None # 90일초과 180일이하
    de180_excess_yy1_below: Optional[int] = None # 180일초과 1년이하
    yy1_excess_yy2_below: Optional[int] = None # 1년초과 2년이하
    yy2_excess_yy3_below: Optional[int] = None # 2년초과 3년이하
    yy3_excess: Optional[int] = None # 3년 초과
    sm: Optional[int] = None # 합계
    stlm_dt: Optional[str] = None # 결산기준일
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "CPOutstandingData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class ShortTermBondsOutstandingData(BaseReportData):
    """단기사채 미상환 잔액 데이터 모델"""

    remndr_exprtn1: Optional[int] = None # 잔여만기
    remndr_exprtn2: Optional[int] = None # 잔여만기
    de10_below: Optional[int] = None # 10일 이하
    de10_excess_de30_below: Optional[int] = None # 10일초과 30일이하
    de30_excess_de90_below: Optional[int] = None # 30일초과 90일이하
    de90_excess_de180_below: Optional[int] = None # 90일초과 180일이하
    de180_excess_yy1_below: Optional[int] = None # 180일초과 1년이하
    sm: Optional[int] = None # 합계
    isu_lmt: Optional[int] = None # 발행 한도
    remndr_lmt: Optional[int] = None # 잔여 한도
    stlm_dt: Optional[str] = None # 결산기준일
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "ShortTermBondsOutstandingData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class CorporateBondsOutstandingData(BaseReportData):
    """회사채 미상환 잔액 데이터 모델"""

    remndr_exprtn1: Optional[int] = None # 잔여만기
    remndr_exprtn2: Optional[int] = None # 잔여만기
    yy1_below: Optional[int] = None # 1년 이하
    yy1_excess_yy2_below: Optional[int] = None # 1년초과 2년이하
    yy2_excess_yy3_below: Optional[int] = None # 2년초과 3년이하
    yy3_excess_yy4_below: Optional[int] = None # 3년초과 4년이하
    yy4_excess_yy5_below: Optional[int] = None # 4년초과 5년이하
    yy5_excess_yy10_below: Optional[int] = None # 5년초과 10년이하
    yy10_excess: Optional[int] = None # 10년초과
    sm: Optional[int] = None # 합계
    stlm_dt: Optional[str] = None # 결산기준일
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "CorporateBondsOutstandingData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class HybridSecuritiesOutstandingData(BaseReportData):
    """신종자본증권 미상환 잔액  데이터 모델"""

    remndr_exprtn1: Optional[int] = None # 잔여만기
    remndr_exprtn2: Optional[int] = None # 잔여만기
    yy1_below: Optional[int] = None # 1년 이하
    yy1_excess_yy5_below: Optional[int] = None # 1년초과 5년이하
    yy5_excess_yy10_below: Optional[int] = None # 5년초과 10년이하
    yy10_excess_yy15_below: Optional[int] = None # 10년초과 15년이하
    yy15_excess_yy20_below: Optional[int] = None # 15년초과 20년이하
    yy20_excess_yy30_below: Optional[int] = None # 20년초과 30년이하
    yy30_excess: Optional[int] = None # 30년초과
    sm: Optional[int] = None # 합계
    stlm_dt: Optional[str] = None # 결산기준일
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "HybridSecuritiesOutstandingData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class CoCoBondsOutstandingData(BaseReportData):
    """조건부 자본증권 미상환 잔액 데이터 모델"""

    remndr_exprtn1: Optional[int] = None # 잔여만기
    remndr_exprtn2: Optional[int] = None # 잔여만기
    yy1_below: Optional[int] = None # 1년 이하
    yy1_excess_yy2_below: Optional[int] = None # 1년초과 2년이하
    yy2_excess_yy3_below: Optional[int] = None # 2년초과 3년이하
    yy3_excess_yy4_below: Optional[int] = None # 3년초과 4년이하
    yy4_excess_yy5_below: Optional[int] = None # 4년초과 5년이하
    yy5_excess_yy10_below: Optional[int] = None # 5년초과 10년이하
    yy10_excess_yy20_below: Optional[int] = None # 10년초과 20년이하
    yy20_excess_yy30_below: Optional[int] = None # 20년초과 30년이하
    yy30_excess: Optional[int] = None # 30년초과
    sm: Optional[int] = None # 합계
    stlm_dt: Optional[str] = None # 결산기준일
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "CoCoBondsOutstandingData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class AuditOpinionsData(BaseReportData):
    """회계감사인의 명칭 및 감사의견 데이터 모델"""

    bsns_year: Optional[str] = None # 사업연도(당기, 전기, 전전기)
    adtor: Optional[str] = None # 감사인
    adt_opinion: Optional[str] = None # 감사의견
    adt_reprt_spcmnt_matter: Optional[str] = None # 감사보고서 특기사항
    emphs_matter: Optional[str] = None # 강조사항 등
    core_adt_matter: Optional[str] = None # 핵심감사사항
    stlm_dt: Optional[str] = None # 결산기준일
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "AuditOpinionsData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class AuditServiceContractsData(BaseReportData):
    """감사용역체결현황 데이터 모델"""

    bsns_year: Optional[str] = None # 사업연도(당기, 전기, 전전기)
    adtor: Optional[str] = None # 감사인
    cn: Optional[str] = None # 내용
    mendng: Optional[int] = None # 보수
    tot_reqre_time: Optional[int] = None # 총소요시간
    adt_cntrct_dtls_mendng: Optional[int] = None # 감사계약내역(보수)
    adt_cntrct_dtls_time: Optional[int] = None # 감사계약내역(시간)
    real_exc_dtls_mendng: Optional[int] = None # 실제수행내역(보수)
    real_exc_dtls_time: Optional[int] = None # 실제수행내역(시간)
    stlm_dt: Optional[str] = None # 결산기준일
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "AuditServiceContractsData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class NonAuditServiceContractsData(BaseReportData):
    """회계감사인과의 비감사용역 계약체결 현황 데이터 모델"""

    bsns_year: Optional[str] = None # 사업연도(당기, 전기, 전전기)
    cntrct_cncls_de: Optional[str] = None # 계약체결일
    servc_cn: Optional[str] = None # 용역내용
    servc_exc_pd: Optional[str] = None # 용역수행기간
    servc_mendng: Optional[int] = None # 용역보수
    rm: Optional[str] = None # 비고
    stlm_dt: Optional[str] = None # 결산기준일
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "NonAuditServiceContractsData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class OutsideDirectorChangesData(BaseReportData):
    """사외이사 및 그 변동현황 데이터 모델"""

    drctr_co: Optional[int] = None # 이사의 수
    otcmp_drctr_co: Optional[int] = None # 사외이사 수
    apnt: Optional[int] = None # 사외이사 변동현황(선임)
    rlsofc: Optional[int] = None # 사외이사 변동현황(해임)
    mdstrm_resig: Optional[int] = None # 사외이사 변동현황(중도퇴임)
    stlm_dt: Optional[str] = None # 결산기준일
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "OutsideDirectorChangesData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class UnregisteredExecutiveCompensationData(BaseReportData):
    """미등기임원 보수현황 데이터 모델"""

    se: Optional[str] = None # 구분	구분(미등기임원)
    nmpr: Optional[int] = None # 인원수
    fyer_salary_totamt: Optional[int] = None # 연간급여 총액
    jan_salary_am: Optional[int] = None # 1인평균 급여액
    rm: Optional[str] = None # 비고
    stlm_dt: Optional[str] = None # 결산기준일
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "UnregisteredExecutiveCompensationData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class ApprovedDirectorCompensationData(BaseReportData):
    """이사·감사 전체의 보수현황(주주총회 승인금액) 데이터 모델"""

    se: Optional[str] = None # 구분	구분(미등기임원)
    nmpr: Optional[int] = None # 인원수
    gmtsck_confm_amount: Optional[int] = None # 주주총회 승인금액
    rm: Optional[str] = None # 비고
    stlm_dt: Optional[str] = None # 결산기준일
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "ApprovedDirectorCompensationData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class CompensationCategoryData(BaseReportData):
    """이사·감사 전체의 보수현황(보수지급금액 - 유형별) 데이터 모델"""

    se: Optional[str] = None # 구분	구분(미등기임원)
    nmpr: Optional[int] = None # 인원수
    pymnt_totamt: Optional[int] = None # 보수총액
    psn1_avrg_pymntamt: Optional[int] = None # 1인당 평균보수액
    rm: Optional[str] = None # 비고
    stlm_dt: Optional[str] = None # 결산기준일
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "CompensationCategoryData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class ProceedsUseData(BaseReportData):
    """공모자금의 사용내역 데이터 모델"""

    se_nm: Optional[str] = None # 구분
    tm: Optional[str] = None # 회차
    pay_de: Optional[str] = None # 납입일
    pay_amount: Optional[int] = None # 납입금액
    on_dclrt_cptal_use_plan: Optional[str] = None # 신고서상 자금사용 계획
    real_cptal_use_sttus: Optional[str] = None # 실제 자금사용 현황
    rs_cptal_use_plan_useprps: Optional[str] = None # 증권신고서 등의 자금사용 계획(사용용도)
    rs_cptal_use_plan_prcure_amount: Optional[int] = None # 증권신고서 등의 자금사용 계획(조달금액)
    real_cptal_use_dtls_cn: Optional[str] = None # 실제 자금사용 내역(내용)
    real_cptal_use_dtls_amount: Optional[int] = None # 실제 자금사용 내역(금액)
    dffrnc_occrrnc_resn: Optional[str] = None # 차이발생 사유 등
    stlm_dt: Optional[str] = None # 결산기준일
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "ProceedsUseData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class PrivateEquityFundsUseData(BaseReportData):
    """사모자금의 사용내역 데이터 모델"""

    se_nm: Optional[str] = None # 구분
    tm: Optional[str] = None # 회차
    pay_de: Optional[str] = None # 납입일
    pay_amount: Optional[int] = None # 납입금액
    on_dclrt_cptal_use_plan: Optional[str] = None # 신고서상 자금사용 계획
    real_cptal_use_sttus: Optional[str] = None # 실제 자금사용 현황
    cptal_use_plan: Optional[str] = None # 자금사용 계획
    mtrpt_cptal_use_plan_useprps: Optional[str] = None # 주요사항보고서의 자금사용 계획(사용용도)
    mtrpt_cptal_use_plan_prcure_amount: Optional[int] = None # 주요사항보고서의 자금사용 계획(조달금액)
    real_cptal_use_dtls_cn: Optional[str] = None # 실제 자금사용 내역(내용)
    real_cptal_use_dtls_amount: Optional[int] = None # 실제 자금사용 내역(금액)
    dffrnc_occrrnc_resn: Optional[str] = None # 차이발생 사유 등
    stlm_dt: Optional[str] = None # 결산기준일
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "PrivateEquityFundsUseData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class BaseFinanceData:
    """재무제표 데이터 베이스 클래스"""
    rcept_no: Optional[str] = None # 접수번호
    reprt_code: Optional[str] = None # 보고서 코드
    bsns_year: Optional[str] = None # 사업 연도
    stock_code: Optional[str] = None # 종목 코드
    corp_code: Optional[str] = None # 고유번호
    sj_div: Optional[str] = None # 재무제표구분	BS:재무상태표, IS:손익계산서
    sj_nm: Optional[str] = None # 재무제표명	ex) 재무상태표 또는 손익계산서 출력
    fs_div: Optional[str] = None # 개별/연결구분	OFS:재무제표, CFS:연결재무제표
    fs_nm: Optional[str] = None # 개별/연결명	ex) 연결재무제표 또는 재무제표 출력
    account_id: Optional[str] = None # 계정ID	계정 고유명칭
    account_nm: Optional[str] = None # 계정명	ex) 자본총계

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

@dataclass
class SingleCompanyMainAccountsData(BaseFinanceData):
    """단일회사 주요계정 데이터 모델"""

    thstrm_nm: Optional[str] = None # 당기명	예) 제 13 기 3분기말
    thstrm_dt: Optional[str] = None # 당기일자	예) 2018.09.30 현재
    thstrm_amount: Optional[int] = None # 당기금액	예) 9,999,999,999
    thstrm_add_amount: Optional[int] = None # 당기누적금액	예) 9,999,999,999
    frmtrm_nm: Optional[str] = None # 전기명	예) 제 12 기말
    frmtrm_dt: Optional[str] = None # 전기일자	예) 2017.01.01 ~ 2017.12.31
    frmtrm_amount: Optional[int] = None # 전기금액	예) 9,999,999,999
    frmtrm_add_amount: Optional[int] = None # 전기누적금액	예) 9,999,999,999
    bfefrmtrm_nm: Optional[str] = None # 전전기명	예) 제 11 기말(※ 사업보고서의 경우에만 출력)
    bfefrmtrm_dt: Optional[str] = None # 전전기일자	예) 2016.12.31 현재(※ 사업보고서의 경우에만 출력)
    bfefrmtrm_amount: Optional[int] = None # 전전기금액	예) 9,999,999,999(※ 사업보고서의 경우에만 출력)
    ord: Optional[int] = None # 계정과목 정렬순서
    currency: Optional[str] = None # 통화 단위

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "SingleCompanyMainAccountsData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class MultiCompanyMainAccountsData(BaseFinanceData):
    """다중회사 주요계정 데이터 모델"""

    thstrm_nm: Optional[str] = None # 당기명	ex) 제 13 기 3분기말
    thstrm_dt: Optional[str] = None # 당기일자	ex) 2018.09.30 현재
    thstrm_amount: Optional[int] = None # 당기금액	9,999,999,999
    thstrm_add_amount: Optional[int] = None # 당기누적금액	9,999,999,999
    frmtrm_nm: Optional[str] = None # 전기명	ex) 제 12 기말
    frmtrm_dt: Optional[str] = None # 전기일자	예) 2017.01.01 ~ 2017.12.31
    frmtrm_amount: Optional[int] = None # 전기금액	9,999,999,999
    frmtrm_add_amount: Optional[int] = None # 전기누적금액	9,999,999,999
    bfefrmtrm_nm: Optional[str] = None # 전전기명	ex) 제 11 기말(※ 사업보고서의 경우에만 출력)
    bfefrmtrm_dt: Optional[str] = None # 전전기일자	ex) 2016.12.31 현재(※ 사업보고서의 경우에만 출력)
    bfefrmtrm_amount: Optional[int] = None # 전전기금액	9,999,999,999(※ 사업보고서의 경우에만 출력)
    ord: Optional[int] = None # 계정과목 정렬순서	계정과목 정렬순서
    currency: Optional[str] = None # 통화 단위

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "MultiCompanyMainAccountsData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class ConsolidatedFinancialStatementsData(BaseFinanceData):
    """단일회사 전체 재무제표 데이터 모델"""

    account_detail: Optional[str] = None # 계정상세
    thstrm_nm: Optional[str] = None # 당기명	예) 제 13 기
    thstrm_amount: Optional[int] = None # 당기금액	예) 9,999,999,999 ※ 분/반기 보고서이면서 (포괄)손익계산서 일 경우 [3개월] 금액
    thstrm_add_amount: Optional[int] = None # 당기누적금액	예) 9,999,999,999
    frmtrm_nm: Optional[str] = None # 전기명	예) 제 12 기말
    frmtrm_amount: Optional[int] = None # 전기금액	예) 9,999,999,999
    frmtrm_q_nm: Optional[str] = None # 전기명(분/반기)	ex) 제 18 기 반기
    frmtrm_q_amount: Optional[int] = None # 전기금액(분/반기)	예) 9,999,999,999 ※ 분/반기 보고서이면서 (포괄)손익계산서 일 경우 [3개월] 금액
    frmtrm_add_amount: Optional[int] = None # 전기누적금액	예) 9,999,999,999
    bfefrmtrm_nm: Optional[str] = None # 전전기명	예) 제 11 기말(※ 사업보고서의 경우에만 출력)
    bfefrmtrm_amount: Optional[int] = None # 전전기금액	예) 9,999,999,999(※ 사업보고서의 경우에만 출력)
    ord: Optional[int] = None # 계정과목 정렬순서
    currency: Optional[str] = None # 통화 단위

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "ConsolidatedFinancialStatementsData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class XBRLTaxonomyFinancialStatementsData(BaseFinanceData):
    """XBRL택사노미재무제표양식 데이터 모델"""

    bsns_de: Optional[str] = None # 기준일	예) 적용 기준일
    label_kor: Optional[str] = None # 한글 출력명
    label_eng: Optional[str] = None # 영문 출력명
    data_tp: Optional[str] = None # 데이터 유형
    ifrs_ref: Optional[str] = None # IFRS Reference

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "XBRLTaxonomyFinancialStatementsData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class SingleCompanyKeyFinancialMetricsData(BaseFinanceData):
    """단일회사 주요 재무지표 데이터 모델"""

    stlm_dt: Optional[str] = None # 결산기준일	예) YYYY-MM-DD
    idx_cl_code: Optional[str] = None # 지표분류코드	예) 수익성지표 : M210000, 안정성지표 : M220000, 성장성지표 : M230000, 활동성지표 : M240000
    idx_cl_nm: Optional[str] = None # 지표분류명	예) 수익성지표,안정성지표,성장성지표,활동성지표
    idx_code: Optional[str] = None # 지표코드	예) M211000
    idx_nm: Optional[str] = None # 지표명	예) 영업이익률
    idx_val: Optional[float] = None # 지표값	예) 0.256

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "SingleCompanyKeyFinancialMetricsData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class MultiCompanyKeyFinancialMetricsData(BaseFinanceData):
    """다중회사 주요 재무지표 데이터 모델"""

    stlm_dt: Optional[str] = None # 결산기준일	예) YYYY-MM-DD
    idx_cl_code: Optional[str] = None # 지표분류코드	예) 수익성지표 : M210000, 안정성지표 : M220000, 성장성지표 : M230000, 활동성지표 : M240000
    idx_cl_nm: Optional[str] = None # 지표분류명	예) 수익성지표,안정성지표,성장성지표,활동성지표
    idx_code: Optional[str] = None # 지표코드	예) M211000
    idx_nm: Optional[str] = None # 지표명	예) 영업이익률
    idx_val: Optional[float] = None # 지표값	예) 0.256

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "MultiCompanyKeyFinancialMetricsData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class BaseOwnershipData:
    """지분공시 데이터 베이스 클래스"""
    
    rcept_no: Optional[str] = None # 접수번호	예) 접수번호(14자리)
    rcept_dt: Optional[str] = None # 접수일자	예) 공시 접수일자(YYYYMMDD)
    corp_code: Optional[str] = None # 고유번호	예) 공시대상회사의 고유번호(8자리)
    corp_name: Optional[str] = None # 회사명	예) 공시대상회사의 종목명(상장사) 또는 법인명(기타법인)
    repror: Optional[str] = None # 대표보고자

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

@dataclass
class MajorShoreholdingsData(BaseOwnershipData):
    """대량보유 상황보고 데이터 모델"""

    report_tp: Optional[str] = None # 보고구분	예) 주식등의 대량보유상황 보고구분
    stkqy: Optional[str] = None # 보유주식등의 수
    stkqy_irds: Optional[str] = None # 보유주식등의 증감
    stkrt: Optional[str] = None # 보유비율
    stkrt_irds: Optional[str] = None # 보유비율 증감
    ctr_stkqy: Optional[str] = None # 주요체결 주식등의 수
    ctr_stkrt: Optional[str] = None # 주요체결 보유비율
    report_resn: Optional[str] = None # 보고사유

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "MajorShoreholdingsData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class InsiderOwnershipData(BaseOwnershipData):
    """임원ㆍ주요주주 소유보고 데이터 모델"""

    isu_exctv_rgist_at: Optional[str] = None # 발행 회사 관계 임원(등기여부)	예) 등기임원, 비등기임원 등
    isu_exctv_ofcps: Optional[str] = None # 발행 회사 관계 임원 직위	예) 대표이사, 이사, 전무 등
    isu_main_shrholdr: Optional[str] = None # 발행 회사 관계 주요 주주	예) 10%이상주주 등
    sp_stock_lmp_cnt: Optional[str] = None # 특정 증권 등 소유 수	예) 9,999,999,999
    sp_stock_lmp_irds_cnt: Optional[str] = None # 특정 증권 등 소유 증감 수	예) 9,999,999,999
    sp_stock_lmp_rate: Optional[str] = None # 특정 증권 등 소유 비율	예) 0.00
    sp_stock_lmp_irds_rate: Optional[str] = None # 특정 증권 등 소유 증감 비율	예) 0.00

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "InsiderOwnershipData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class BaseRegistrationData:
    """지분공시 데이터 베이스 클래스"""
    
    rcept_no: Optional[str] = None # 접수번호	예) 접수번호(14자리)
    corp_cls: Optional[CorpClass] = None # 법인구분	예) 법인구분 : Y(유가), K(코스닥), N(코넥스), E(기타)
    corp_code: Optional[str] = None # 고유번호	예) 공시대상회사의 고유번호(8자리)
    corp_name: Optional[str] = None # 회사명	예) 공시대상회사명
    tm: Optional[str] = None # 회차

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

@dataclass
class RegistrationGeneralData(BaseRegistrationData):
    """일반사항"""

    title: Optional[str] = "일반사항"
    bdnmn: Optional[str] = None # 채무증권 명칭
    slmth: Optional[str] = None # 모집(매출)방법
    fta: Optional[int] = None # 권면(전자등록)총액	예) 9,999,999,999
    slta: Optional[int] = None # 모집(매출)총액	예) 9,999,999,999
    isprc: Optional[int] = None # 발행가액	예) 9,999,999,999
    intr: Optional[int] = None # 이자율
    isrr: Optional[int] = None # 발행수익률
    rpd: Optional[str] = None # 상환기일
    print_pymint: Optional[str] = None # 원리금지급대행기관
    mngt_cmp: Optional[str] = None # (사채)관리회사
    cdrt_int: Optional[str] = None # 신용등급(신용평가기관)

    sbd: Optional[str] = None # 청약기일
    pymd: Optional[str] = None # 납입기일
    sband: Optional[str] = None # 청약공고일
    asand: Optional[str] = None # 배정공고일
    asstd: Optional[str] = None # 배정기준일
    exstk: Optional[str] = None # 신주인수권에 관한 사항(행사대상증권)
    exprc: Optional[int] = None # 신주인수권에 관한 사항(행사가격)	예) 9,999,999,999
    expd: Optional[str] = None # 신주인수권에 관한 사항(행사기간)
    rpt_rcpn: Optional[str] = None # 주요사항보고서(접수번호)

    dpcrn: Optional[str] = None # 표시통화
    dpcr_amt: Optional[int] = None # 표시통화기준발행규모
    usarn: Optional[str] = None # 사용지역
    usntn: Optional[str] = None # 사용국가
    wnexpl_at: Optional[str] = None # 원화 교환 예정 여부
    udtintnm: Optional[str] = None # 인수기관명
    grt_int: Optional[str] = None # 보증을 받은 경우(보증기관)
    grt_amt: Optional[int] = None # 보증을 받은 경우(보증금액)	예) 9,999,999,999
    icmg_mgknd: Optional[str] = None # 담보 제공의 경우(담보의 종류)
    icmg_mgamt: Optional[int] = None # 담보 제공의 경우(담보금액)	예) 9,999,999,999
    estk_exstk: Optional[str] = None # 지분증권과 연계된 경우(행사대상증권)
    estk_exrt: Optional[str] = None # 지분증권과 연계된 경우(권리행사비율)
    estk_exprc: Optional[int] = None # 지분증권과 연계된 경우(권리행사가격)	예) 9,999,999,999
    estk_expd: Optional[str] = None # 지분증권과 연계된 경우(권리행사기간)
    rpt_rcpn: Optional[str] = None # 주요사항보고서(접수번호)
    drcb_at: Optional[str] = None # 파생결합사채해당여부
    drcb_uast: Optional[str] = None # 파생결합사채(기초자산)
    drcb_optknd: Optional[str] = None # 파생결합사채(옵션종류)
    drcb_mtd: Optional[str] = None # 파생결합사채(만기일)

    stn: Optional[str] = None # 형태
    bddd: Optional[str] = None # 이사회 결의일
    ctrd: Optional[str] = None # 계약일
    gmtsck_shddstd: Optional[str] = None # 주주총회를 위한 주주확정일
    ap_gmtsck: Optional[str] = None # 승인을 위한 주주총회일
    aprskh_pd_bgd: Optional[str] = None # 주식매수청구권 행사 기간 및 가격(시작일)
    aprskh_pd_edd: Optional[str] = None # 주식매수청구권 행사 기간 및 가격(종료일)
    aprskh_prc: Optional[str] = None # 주식매수청구권 행사 기간 및 가격((주식매수청구가격-회사제시))
    mgdt_etc: Optional[str] = None # 합병기일등
    rt_vl: Optional[str] = None # 비율 또는 가액
    exevl_int: Optional[str] = None # 외부평가기관
    grtmn_etc: Optional[str] = None # 지급 교부금 등

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "RegistrationGeneralData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class RegistrationStockData(BaseRegistrationData):
    """증권의 종류"""

    title: Optional[str] = "증권의종류"
    stksen: Optional[str] = None # 증권의종류
    stkcnt: Optional[int] = None # 증권수량	예) 9,999,999,999
    fv: Optional[int] = None # 액면가액	예) 9,999,999,999
    slprc: Optional[int] = None # 모집(매출)가액	예) 9,999,999,999
    slta: Optional[int] = None # 모집(매출)총액	예) 9,999,999,999
    slmthn: Optional[str] = None # 모집(매출)방법	예) 모집(매출)방법

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "RegistrationStockData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class RegistrationAcquirerCData(BaseRegistrationData):
    """인수인 정보"""

    title: Optional[str] = "인수인정보"
    actsen: Optional[str] = None # 인수인구분
    actnmn: Optional[str] = None # 인수인명
    stksen: Optional[str] = None # 증권의종류
    udtcnt: Optional[int] = None # 인수수량	예) 9,999,999,999
    udtamt: Optional[int] = None # 인수금액	예) 9,999,999,999
    udtprc: Optional[int] = None # 인수대가
    udtmth: Optional[str] = None # 인수방법

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "RegistrationAcquirerCData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class RegistrationPurposeData(BaseRegistrationData):
    """자금의 사용목적"""

    title: Optional[str] = "자금의사용목적"
    se: Optional[str] = None # 구분
    amt: Optional[int] = None # 금액	예) 9,999,999,999

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "RegistrationPurposeData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class RegistrationShareholderData(BaseRegistrationData):
    """매출인에 관한사항"""

    title: Optional[str] = "매출인에관한사항"
    hdr: Optional[str] = None # 보유자
    rl_cmp: Optional[str] = None # 회사와의관계
    bfsl_hdstk: Optional[int] = None # 매출전보유증권수	예) 9,999,999,999
    slstk: Optional[int] = None # 매출증권수	예) 9,999,999,999
    atsl_hdstk: Optional[int] = None # 매출후보유증권수	예) 9,999,999,999

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "RegistrationShareholderData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class RegistrationPutBackOptionData(BaseRegistrationData):
    """일반 청약자 환매청구권"""

    title: Optional[str] = "일반청약자환매청구권"
    grtrs: Optional[str] = None # 부여사유
    exavivr: Optional[str] = None # 행사가능 투자자
    grtcnt: Optional[int] = None # 부여수량	예) 9,999,999,999
    expd: Optional[str] = None # 행사기간
    exprc: Optional[int] = None # 행사가격	예) 9,999,999,999

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "RegistrationPutBackOptionData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class RegistrationIssuedSecuritiesData(BaseRegistrationData):
    """발행증권"""

    title: Optional[str] = "발행증권"
    kndn: Optional[str] = None # 종류
    cnt: Optional[int] = None # 수량	예) 9,999,999,999
    fv: Optional[int] = None # 액면가액	예) 9,999,999,999
    slprc: Optional[int] = None # 모집(매출)가액	예) 9,999,999,999
    slta: Optional[int] = None # 모집(매출)총액	예) 9,999,999,999

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "RegistrationIssuedSecuritiesData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class RegistrationCompanyData(BaseRegistrationData):
    """당사 회사에 관한 사항"""

    title: Optional[str] = "당사회사에관한사항" # 제목
    cmpnm: Optional[str] = None # 회사명
    sen: Optional[str] = None # 구분
    tast: Optional[int] = None # 총자산	예) 9,999,999,999
    cpt: Optional[int] = None # 자본금	예) 9,999,999,999
    isstk_knd: Optional[str] = None # 발행주식수(주식의종류)
    isstk_cnt: Optional[int] = None # 발행주식수(주식수)	예) 9,999,999,999

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "RegistrationCompanyData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class RegistrationEquitySecuritiesData(BaseRegistrationData):
    """지분증권"""

    title: Optional[str] = "지분증권" # 제목
    generals: List[RegistrationGeneralData] = field(default_factory=list) # 일반사항
    stocks: List[RegistrationStockData] = field(default_factory=list) # 증권의종류
    acquirers: List[RegistrationAcquirerCData] = field(default_factory=list) # 인수인 정보
    purposes: List[RegistrationPurposeData] = field(default_factory=list) # 자금의 사용목적
    shareholders: List[RegistrationShareholderData] = field(default_factory=list) # 매출인에 관한사항
    put_back_options: List[RegistrationPutBackOptionData] = field(default_factory=list) # 일반 청약자 환매청구권

    @classmethod
    def from_raw_data(cls, raw_data: Dict) -> "RegistrationEquitySecuritiesData":
        """딕셔너리에서 데이터 클래스 생성"""
        for item in raw_data.get("group", {}):
            title = item.get("title", "")
            list = item.get("list", [])

            if title == "일반사항":
                generals = [RegistrationGeneralData.from_raw_data(item) for item in list]
                cls.generals = generals
            elif title == "증권의종류":
                stocks = [RegistrationStockData.from_raw_data(item) for item in list]
                cls.stocks = stocks
            elif title == "인수인정보":
                acquirers = [RegistrationAcquirerCData.from_raw_data(item) for item in list]
                cls.acquirers = acquirers
            elif title == "자금의사용목적":
                purposes = [RegistrationPurposeData.from_raw_data(item) for item in list]
                cls.purposes = purposes
            elif title == "매출인에관한사항":
                shareholders = [RegistrationShareholderData.from_raw_data(item) for item in list]
                cls.shareholders = shareholders
            elif title == "일반청약자환매청구권":
                put_back_options = [RegistrationPutBackOptionData.from_raw_data(item) for item in list]
                cls.put_back_options = put_back_options
        
        return cls

@dataclass
class RegistrationStatementData(BaseRegistrationData):
    """증권신고서"""

    title: Optional[str] = "증권신고서"
    generals: List[RegistrationGeneralData] = field(default_factory=list) # 일반사항
    acquirers: List[RegistrationAcquirerCData] = field(default_factory=list) # 인수인 정보
    purposes: List[RegistrationPurposeData] = field(default_factory=list) # 자금의 사용목적
    shareholders: List[RegistrationShareholderData] = field(default_factory=list) # 매출인에 관한사항

    @classmethod
    def from_raw_data(cls, raw_data: Dict) -> "RegistrationStatementData":
        """딕셔너리에서 데이터 클래스 생성"""
        for item in raw_data.get("group", {}):
            title = item.get("title", "")
            list = item.get("list", [])

            if title == "일반사항":
                generals = [RegistrationGeneralData.from_raw_data(item) for item in list]
                cls.generals = generals
            elif title == "인수인정보":
                acquirers = [RegistrationAcquirerCData.from_raw_data(item) for item in list]
                cls.acquirers = acquirers
            elif title == "자금의사용목적":
                purposes = [RegistrationPurposeData.from_raw_data(item) for item in list]
                cls.purposes = purposes
            elif title == "매출인에관한사항":
                shareholders = [RegistrationShareholderData.from_raw_data(item) for item in list]
                cls.shareholders = shareholders
        
        return cls

@dataclass
class RegistrationDepositoryReceiptData(BaseRegistrationData):
    """증권예탁증권"""

    title: Optional[str] = "증권예탁증권"
    generals: List[RegistrationGeneralData] = field(default_factory=list) # 일반사항
    stocks: List[RegistrationStockData] = field(default_factory=list) # 증권의종류
    acquirers: List[RegistrationAcquirerCData] = field(default_factory=list) # 인수인 정보
    purposes: List[RegistrationPurposeData] = field(default_factory=list) # 자금의 사용목적
    shareholders: List[RegistrationShareholderData] = field(default_factory=list) # 매출인에 관한사항

    @classmethod
    def from_raw_data(cls, raw_data: Dict) -> "RegistrationDepositoryReceiptData":
        """딕셔너리에서 데이터 클래스 생성"""
        for item in raw_data.get("group", {}):
            title = item.get("title", "")
            list = item.get("list", [])

            if title == "일반사항":
                generals = [RegistrationGeneralData.from_raw_data(item) for item in list]
                cls.generals = generals
            elif title == "증권의종류":
                stocks = [RegistrationStockData.from_raw_data(item) for item in list]
                cls.stocks = stocks
            elif title == "인수인정보":
                acquirers = [RegistrationAcquirerCData.from_raw_data(item) for item in list]
                cls.acquirers = acquirers
            elif title == "자금의사용목적":
                purposes = [RegistrationPurposeData.from_raw_data(item) for item in list]
                cls.purposes = purposes
            elif title == "매출인에관한사항":
                shareholders = [RegistrationShareholderData.from_raw_data(item) for item in list]
                cls.shareholders = shareholders
        
        return cls

@dataclass
class RegistrationMergedData(BaseRegistrationData):
    """합병"""

    title: Optional[str] = "합병"
    generals: List[RegistrationGeneralData] = field(default_factory=list) # 일반사항
    issued_securities: List[RegistrationIssuedSecuritiesData] = field(default_factory=list) # 발행증권
    companies: List[RegistrationCompanyData] = field(default_factory=list) # 당사 회사에 관한 사항

    @classmethod
    def from_raw_data(cls, raw_data: Dict) -> "RegistrationMergedData":
        """딕셔너리에서 데이터 클래스 생성"""
        for item in raw_data.get("group", {}):
            title = item.get("title", "")
            list = item.get("list", [])

            if title == "일반사항":
                generals = [RegistrationGeneralData.from_raw_data(item) for item in list]
                cls.generals = generals
            elif title == "발행증권":
                issued_securities = [RegistrationIssuedSecuritiesData.from_raw_data(item) for item in list]
                cls.issued_securities = issued_securities
            elif title == "당사회사에관한사항":
                companies = [RegistrationCompanyData.from_raw_data(item) for item in list]
                cls.companies = companies
        
        return cls(generals=generals, issued_securities=issued_securities, companies=companies)

@dataclass
class RegistrationShareExchangeData(BaseRegistrationData):
    """주식의 포괄적 교환·이전"""

    title: Optional[str] = "주식의포괄적교환·이전"
    generals: List[RegistrationGeneralData] = field(default_factory=list) # 일반사항
    issued_securities: List[RegistrationIssuedSecuritiesData] = field(default_factory=list) # 발행증권
    companies: List[RegistrationCompanyData] = field(default_factory=list) # 당사 회사에 관한 사항

    @classmethod
    def from_raw_data(cls, raw_data: Dict) -> "RegistrationShareExchangeData":
        """딕셔너리에서 데이터 클래스 생성"""
        for item in raw_data.get("group", {}):
            title = item.get("title", "")
            list = item.get("list", [])

            if title == "일반사항":
                generals = [RegistrationGeneralData.from_raw_data(item) for item in list]
                cls.generals = generals
            elif title == "발행증권":
                issued_securities = [RegistrationIssuedSecuritiesData.from_raw_data(item) for item in list]
                cls.issued_securities = issued_securities
            elif title == "당사회사에관한사항":
                companies = [RegistrationCompanyData.from_raw_data(item) for item in list]
                cls.companies = companies
        
        return cls

@dataclass
class RegistrationSplitData(BaseRegistrationData):
    """분할"""

    title: Optional[str] = "분할"
    generals: List[RegistrationGeneralData] = field(default_factory=list) # 일반사항
    issued_securities: List[RegistrationIssuedSecuritiesData] = field(default_factory=list) # 발행증권
    companies: List[RegistrationCompanyData] = field(default_factory=list) # 당사 회사에 관한 사항

    @classmethod
    def from_raw_data(cls, raw_data: Dict) -> "RegistrationSplitData":
        """딕셔너리에서 데이터 클래스 생성"""
        for item in raw_data.get("group", []):
            title = item.get("title", "")
            list = item.get("list", [])


            if title == "일반사항":
                generals = [RegistrationGeneralData.from_raw_data(item) for item in list]
                cls.generals = generals
            elif title == "발행증권":
                issued_securities = [RegistrationIssuedSecuritiesData.from_raw_data(item) for item in list]
                cls.issued_securities = issued_securities
            elif title == "당사회사에관한사항":
                companies = [RegistrationCompanyData.from_raw_data(item) for item in list]
                cls.companies = companies
        
        return cls
