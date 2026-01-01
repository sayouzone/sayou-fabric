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

class ReportCode(Enum):
    """보고서 코드"""
    BUSINESS_REPORT = "11011"      # 사업보고서
    FIRST_QUARTER_REPORT = "11012"     # 1분기보고서
    SECOND_QUARTER_REPORT = "11013"      # 2분기보고서
    THIRD_QUARTER_REPORT = "11014"        # 3분기보고서
    YEAR_REPORT = "11015"        # 사업보고서

    @classmethod
    def from_value(cls, value: Optional[str]) -> Optional["ReportCode"]:
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
            "11011": "사업보고서",
            "11012": "1분기보고서",
            "11013": "2분기보고서",
            "11014": "3분기보고서",
            "11015": "사업보고서",
        }
        return names.get(self.value, "알 수 없음")

class FinancialStatementCategory(Enum):
    """재무제표 구분"""

    BS1 = "재무상태표", "연결", "유동/비유동법"
    BS2 = "재무상태표", "개별", "유동/비유동법"
    BS3 = "재무상태표", "연결", "유동성배열법"
    BS4 = "재무상태표", "개별", "유동성배열법"
    IS1 = "별개의 손익계산서", "연결", "기능별분류"
    IS2 = "별개의 손익계산서", "개별", "기능별분류"
    IS3 = "별개의 손익계산서", "연결", "성격별분류"
    IS4 = "별개의 손익계산서", "개별", "성격별분류"
    CIS1 = "포괄손익계산서", "연결", "세후"
    CIS2 = "포괄손익계산서", "개별", "세후"
    CIS3 = "포괄손익계산서", "연결", "세전"
    CIS4 = "포괄손익계산서", "개별", "세전"
    
    DCIS1 = "단일 포괄손익계산서", "연결", "기능별분류", "세후포괄손익"
    DCIS2 = "단일 포괄손익계산서", "개별", "기능별분류", "세후포괄손익"
    DCIS3 = "단일 포괄손익계산서", "연결", "기능별분류", "세전"
    DCIS4 = "단일 포괄손익계산서", "개별", "기능별분류", "세전"
    DCIS5 = "단일 포괄손익계산서", "연결", "성격별분류", "세후포괄손익"
    DCIS6 = "단일 포괄손익계산서", "개별", "성격별분류", "세후포괄손익"
    DCIS7 = "단일 포괄손익계산서", "연결", "성격별분류", "세전"
    DCIS8 = "단일 포괄손익계산서", "개별", "성격별분류", "세전"
    
    CF1 = "현금흐름표", "연결", "직접법"
    CF2 = "현금흐름표", "개별", "직접법"
    CF3 = "현금흐름표", "연결", "간접법"
    CF4 = "현금흐름표", "개별", "간접법"
    SCE1 = "자본변동표", "연결"
    SCE2 = "자본변동표", "개별"

    @classmethod
    def from_value(cls, value: Optional[str]) -> Optional["FinancialStatementCategory"]:
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
            "BS1": "재무상태표",
            "BS2": "재무상태표",
            "BS3": "재무상태표",
            "BS4": "재무상태표",
            "IS1": "별개의 손익계산서",
            "IS2": "별개의 손익계산서",
            "IS3": "별개의 손익계산서",
            "IS4": "별개의 손익계산서",
            "CIS1": "포괄손익계산서",
            "CIS2": "포괄손익계산서",
            "CIS3": "포괄손익계산서",
            "CIS4": "포괄손익계산서",
            "DCIS1": "단일 포괄손익계산서",
            "DCIS2": "단일 포괄손익계산서",
            "DCIS3": "단일 포괄손익계산서",
            "DCIS4": "단일 포괄손익계산서",
        }
        return names.get(self.value, "알 수 없음")

@dataclass
class OpenDartRequest:
    """증권신고서 주요정보 요청 클래스"""

    crtfc_key: str # API 인증키	예) 발급받은 인증키(40자리)
    corp_code: str # 고유번호	예) 공시대상회사의 고유번호(8자리)
    bsns_year: Optional[str] = None # 사업연도	예) 사업연도(4자리) ※ 2015년 이후 부터 정보제공
    bgn_de: Optional[str] = None # 시작일(최초접수일)	예) 검색시작 접수일자(YYYYMMDD) ※ 2015년 이후 부터 정보제공
    end_de: Optional[str] = None # 종료일(최초접수일)	예) 검색종료 접수일자(YYYYMMDD) ※ 2015년 이후 부터 정보제공
    reprt_code: Optional[ReportCode] = None # 보고서 코드	예) 사업보고서 : 1분기보고서 : 11013, 반기보고서 : 11012, 3분기보고서 : 11014, 사업보고서 : 11011
    fs_div: Optional[str] = None # 재무제표구분	예) 재무제표구분 : OFS(재무제표), CFS(연결재무제표)
    sj_div: Optional[str] = None # 재무제표구분	예) BS1
    idx_cl_code: Optional[str] = None # 지표분류코드	예) 수익성지표 : M210000, 안정성지표 : M220000, 성장성지표 : M230000, 활동성지표 : M240000
    corp_cls: Optional[str] = None
    page_no: Optional[int] = None
    page_count: Optional[int] = None
    
    def to_params(self) -> Dict[str, Any]:
        """API 호출용 파라미터로 변환"""
        params = {
            "crtfc_key": self.crtfc_key,
            "corp_code": self.corp_code,
        }

        if self.bsns_year: params["bsns_year"] = self.bsns_year
        if self.bgn_de: params["bgn_de"] = self.bgn_de
        if self.end_de: params["end_de"] = self.end_de
        if self.reprt_code: params["reprt_code"] = self.reprt_code
        if self.fs_div: params["fs_div"] = self.fs_div
        if self.sj_div: params["sj_div"] = self.sj_div
        if self.idx_cl_code: params["idx_cl_code"] = self.idx_cl_code
        if self.corp_cls: params["corp_cls"] = self.corp_cls
        if self.page_no: params["page_no"] = self.page_no
        if self.page_count: params["page_count"] = self.page_count

        return params

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

@dataclass
class BaseMaterialFactsData:
    """주요사항보고서 주요정보 데이터 베이스 클래스"""
    
    rcept_no: Optional[str] = None # 접수번호	예) 접수번호(14자리)
    corp_cls: Optional[CorpClass] = None # 법인구분	예) 법인구분 : Y(유가), K(코스닥), N(코넥스), E(기타)
    corp_code: Optional[str] = None # 고유번호	예) 공시대상회사의 고유번호(8자리)
    corp_name: Optional[str] = None # 회사명	예) 공시대상회사명

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

@dataclass
class PutOptionData(BaseMaterialFactsData):
    """자산양수도(기타), 풋백옵션"""

    rp_rsn: Optional[str] = None # 보고 사유
    ast_inhtrf_prc: Optional[int] = None # 자산양수ㆍ도 가액	예) 9,999,999,999

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "PutOptionData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class BankruptcyData(BaseMaterialFactsData):
    """부도발생"""

    df_cn: Optional[str] = None # 부도내용
    df_amt: Optional[int] = None # 부도금액	예) 9,999,999,999
    df_bnk: Optional[str] = None # 부도발생은행
    dfd: Optional[str] = None # 최종부도(당좌거래정지)일자
    df_rs: Optional[str] = None # 부도사유 및 경위

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "BankruptcyData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class SuspensionData(BaseMaterialFactsData):
    """영업정지"""

    bsnsp_rm: Optional[str] = None # 영업정지 분야
    bsnsp_amt: Optional[int] = None # 영업정지 내역(영업정지금액)	예) 9,999,999,999
    rsl: Optional[int] = None # 영업정지 내역(최근매출총액)	예) 9,999,999,999
    sl_vs: Optional[str] = None # 영업정지 내역(매출액 대비)
    ls_atn: Optional[str] = None # 영업정지 내역(대규모법인여부)
    krx_stt_atn: Optional[str] = None # 영업정지 내역(거래소 의무공시 해당 여부)
    bsnsp_cn: Optional[str] = None # 영업정지 내용
    bsnsp_rs: Optional[str] = None # 영업정지사유
    ft_ctp: Optional[str] = None # 향후대책
    bsnsp_af: Optional[str] = None # 영업정지영향
    bsnspd: Optional[str] = None # 영업정지일자
    bddd: Optional[str] = None # 이사회결의일(결정일)
    od_a_at_t: Optional[int] = None # 사외이사 참석여부(참석)	예) 9,999,999,999
    od_a_at_b: Optional[int] = None # 사외이사 참석여부(불참)	예) 9,999,999,999
    adt_a_atn: Optional[str] = None # 감사(감사위원) 참석여부

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "SuspensionData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class RehabilitationData(BaseMaterialFactsData):
    """회생절차 개시신청"""
    
    apcnt: Optional[str] = None # 신청인 (회사와의 관계)
    cpct: Optional[str] = None # 관할법원
    rq_rs: Optional[str] = None # 신청사유
    rqd: Optional[str] = None # 신청일자
    ft_ctp_sc: Optional[str] = None # 향후대책 및 일정

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "RehabilitationData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class DissolutionData(BaseMaterialFactsData):
    """해산사유 발생"""
    
    ds_rs: Optional[str] = None # 해산사유
    ds_rsd: Optional[str] = None # 해산사유발생일(결정일)
    od_a_at_t: Optional[int] = None # 사외이사 참석여부(참석)	예) 9,999,999,999
    od_a_at_b: Optional[int] = None # 사외이사 참석여부(불참)	예) 9,999,999,999
    adt_a_atn: Optional[str] = None # 감사(감사위원) 참석 여부

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "DissolutionData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class RightsIssueData(BaseMaterialFactsData):
    """유상증자 결정"""
    
    nstk_ostk_cnt: Optional[int] = None # 신주의 종류와 수(보통주식 (주))	예) 9,999,999,999
    nstk_estk_cnt: Optional[int] = None # 신주의 종류와 수(기타주식 (주))	예) 9,999,999,999
    fv_ps: Optional[int] = None # 1주당 액면가액 (원)	예) 9,999,999,999
    bfic_tisstk_ostk: Optional[int] = None # 증자전 발행주식총수 (주)(보통주식 (주))	예) 9,999,999,999
    bfic_tisstk_estk: Optional[int] = None # 증자전 발행주식총수 (주)(기타주식 (주))	예) 9,999,999,999
    fdpp_fclt: Optional[int] = None # 자금조달의 목적(시설자금 (원))	예) 9,999,999,999
    fdpp_bsninh: Optional[int] = None # 자금조달의 목적(영업양수자금 (원))	예) 9,999,999,999
    fdpp_op: Optional[int] = None # 자금조달의 목적(운영자금 (원))	예) 9,999,999,999
    fdpp_dtrp: Optional[int] = None # 자금조달의 목적(채무상환자금 (원))	예) 9,999,999,999
    fdpp_ocsa: Optional[int] = None # 자금조달의 목적(타법인 증권 취득자금 (원))	예) 9,999,999,999
    fdpp_etc: Optional[int] = None # 자금조달의 목적(기타자금 (원))	예) 9,999,999,999
    ic_mthn: Optional[str] = None # 증자방식
    ssl_at: Optional[str] = None # 공매도 해당여부
    ssl_bgd: Optional[str] = None # 공매도 시작일
    ssl_edd: Optional[str] = None # 공매도 종료일

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "BonusIssueData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class BonusIssueData(BaseMaterialFactsData):
    """무상증자 결정"""
    
    nstk_ostk_cnt: Optional[int] = None # 신주의 종류와 수(보통주식 (주))	예) 9,999,999,999
    nstk_estk_cnt: Optional[int] = None # 신주의 종류와 수(기타주식 (주))	예) 9,999,999,999
    fv_ps: Optional[int] = None # 1주당 액면가액 (원)	예) 9,999,999,999
    bfic_tisstk_ostk: Optional[int] = None # 증자전 발행주식총수 (주)(보통주식 (주))	예) 9,999,999,999
    bfic_tisstk_estk: Optional[int] = None # 증자전 발행주식총수 (주)(기타주식 (주))	예) 9,999,999,999
    nstk_asstd: Optional[str] = None # 신주배정기준일
    nstk_ascnt_ps_ostk: Optional[int] = None # 1주당 신주배정 주식수(보통주식 (주))	예) 9,999,999,999.9x (소수점 최대 20자리)
    nstk_ascnt_ps_estk: Optional[int] = None # 1주당 신주배정 주식수(기타주식 (주))	예) 9,999,999,999.9x (소수점 최대 20자리)
    nstk_dividrk: Optional[str] = None # 신주의 배당기산일
    nstk_dlprd: Optional[str] = None # 신주권교부예정일
    nstk_lstprd: Optional[str] = None # 신주의 상장 예정일
    bddd: Optional[str] = None # 이사회결의일(결정일)
    od_a_at_t: Optional[int] = None # 사외이사 참석여부(참석(명))	예) 9,999,999,999
    od_a_at_b: Optional[int] = None # 사외이사 참석여부(불참(명))	예) 9,999,999,999
    adt_a_atn: Optional[str] = None # 감사(감사위원)참석 여부

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "BonusIssueData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class IssueIncreaseData(BaseMaterialFactsData):
    """유무상증자 결정"""
    
    piic_nstk_ostk_cnt: Optional[int] = None # 유상증자(신주의 종류와 수(보통주식 (주)))	예) 9,999,999,999
    piic_nstk_estk_cnt: Optional[int] = None # 유상증자(신주의 종류와 수(기타주식 (주)))	예) 9,999,999,999
    piic_fv_ps: Optional[int] = None # 유상증자(1주당 액면가액 (원))	예) 9,999,999,999
    piic_bfic_tisstk_ostk: Optional[int] = None # 유상증자(증자전 발행주식총수 (주)(보통주식 (주)))	예) 9,999,999,999
    piic_bfic_tisstk_estk: Optional[int] = None # 유상증자(증자전 발행주식총수 (주)(기타주식 (주)))	예) 9,999,999,999
    piic_fdpp_fclt: Optional[int] = None # 유상증자(자금조달의 목적(시설자금 (원)))	예) 9,999,999,999
    piic_fdpp_bsninh: Optional[int] = None # 유상증자(자금조달의 목적(영업양수자금 (원)))	예) 9,999,999,999
    piic_fdpp_op: Optional[int] = None # 유상증자(자금조달의 목적(운영자금 (원)))	예) 9,999,999,999
    piic_fdpp_dtrp: Optional[int] = None # 유상증자(자금조달의 목적(채무상환자금 (원)))	예) 9,999,999,999
    piic_fdpp_ocsa: Optional[int] = None # 유상증자(자금조달의 목적(타법인 증권 취득자금 (원)))	예) 9,999,999,999
    piic_fdpp_etc: Optional[int] = None # 유상증자(자금조달의 목적(기타자금 (원)))	예) 9,999,999,999
    piic_ic_mthn: Optional[str] = None # 유상증자(증자방식)	유상증자(증자방식)
    fric_nstk_ostk_cnt: Optional[int] = None # 무상증자(신주의 종류와 수(보통주식 (주)))	예) 9,999,999,999
    fric_nstk_estk_cnt: Optional[int] = None # 무상증자(신주의 종류와 수(기타주식 (주)))	예) 9,999,999,999
    fric_fv_ps: Optional[int] = None # 무상증자(1주당 액면가액 (원))	예) 9,999,999,999
    fric_bfic_tisstk_ostk: Optional[int] = None # 무상증자(증자전 발행주식총수(보통주식 (주)))	예) 9,999,999,999
    fric_bfic_tisstk_estk: Optional[int] = None # 무상증자(증자전 발행주식총수(기타주식 (주)))	예) 9,999,999,999
    fric_nstk_asstd: Optional[str] = None # 무상증자(신주배정기준일)
    fric_nstk_ascnt_ps_ostk: Optional[int] = None # 무상증자(1주당 신주배정 주식수(보통주식 (주)))	예) 9,999,999,999.9x (소수점 최대 20자리)
    fric_nstk_ascnt_ps_estk: Optional[int] = None # 무상증자(1주당 신주배정 주식수(기타주식 (주)))	예) 9,999,999,999.9x (소수점 최대 20자리)
    fric_nstk_dividrk: Optional[str] = None # 무상증자(신주의 배당기산일)
    fric_nstk_dlprd: Optional[str] = None # 무상증자(신주권교부예정일)
    fric_nstk_lstprd: Optional[str] = None # 무상증자(신주의 상장 예정일)
    fric_bddd: Optional[str] = None # 무상증자(이사회결의일(결정일))
    fric_od_a_at_t: Optional[int] = None # 무상증자(사외이사 참석여부(참석(명)))	예) 9,999,999,999
    fric_od_a_at_b: Optional[int] = None # 무상증자(사외이사 참석여부(불참(명)))	예) 9,999,999,999
    fric_adt_a_atn: Optional[str] = None # 무상증자(감사(감사위원)참석 여부)
    ssl_at: Optional[str] = None # 공매도 해당여부
    ssl_bgd: Optional[str] = None # 공매도 시작일
    ssl_edd: Optional[str] = None # 공매도 종료일

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "BonusIssueData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class CapitalReductionData(BaseMaterialFactsData):
    """감자 결정"""
    crstk_ostk_cnt: Optional[int] = None # 감자주식의 종류와 수(보통주식 (주))	예) 9,999,999,999
    crstk_estk_cnt: Optional[int] = None # 감자주식의 종류와 수(기타주식 (주))	예) 9,999,999,999
    fv_ps: Optional[int] = None # 1주당 액면가액 (원)	예) 9,999,999,999
    bfcr_cpt: Optional[int] = None # 감자전후 자본금(감자전 (원))	예) 9,999,999,999
    atcr_cpt: Optional[int] = None # 감자전후 자본금(감자후 (원))	예) 9,999,999,999
    bfcr_tisstk_ostk: Optional[int] = None # 감자전후 발행주식수(보통주식 (주)(감자전 (원)))	예) 9,999,999,999
    atcr_tisstk_ostk: Optional[int] = None # 감자전후 발행주식수(보통주식 (주)(감자후 (원)))	예) 9,999,999,999
    bfcr_tisstk_estk: Optional[int] = None # 감자전후 발행주식수(기타주식 (주)(감자전 (원)))	예) 9,999,999,999
    atcr_tisstk_estk: Optional[int] = None # 감자전후 발행주식수(기타주식 (주)(감자후 (원)))	예) 9,999,999,999
    cr_rt_ostk: Optional[int] = None # 감자비율(보통주식 (%))
    cr_rt_estk: Optional[int] = None # 감자비율(기타주식 (%))
    cr_std: Optional[str] = None # 감자기준일
    cr_mth: Optional[str] = None # 감자방법
    cr_rs: Optional[str] = None # 감자사유
    crsc_gmtsck_prd: Optional[str] = None # 감자일정(주주총회 예정일)
    crsc_trnmsppd: Optional[str] = None # 감자일정(명의개서정지기간)
    crsc_osprpd: Optional[str] = None # 감자일정(구주권 제출기간)
    crsc_trspprpd: Optional[str] = None # 감자일정(매매거래 정지예정기간)
    crsc_osprpd_bgd: Optional[str] = None # 감자일정(구주권 제출기간(시작일))
    crsc_osprpd_edd: Optional[str] = None # 감자일정(구주권 제출기간(종료일))
    crsc_trspprpd_bgd: Optional[str] = None # 감자일정(매매거래 정지예정기간(시작일))
    crsc_trspprpd_edd: Optional[str] = None # 감자일정(매매거래 정지예정기간(종료일))
    crsc_nstkdlprd: Optional[str] = None # 감자일정(신주권교부예정일)
    crsc_nstklstprd: Optional[str] = None # 감자일정(신주상장예정일)
    cdobprpd_bgd: Optional[str] = None # 채권자 이의제출기간(시작일)
    cdobprpd_edd: Optional[str] = None # 채권자 이의제출기간(종료일)
    ospr_nstkdl_pl: Optional[str] = None # 구주권제출 및 신주권교부장소
    bddd: Optional[str] = None # 이사회결의일(결정일)
    od_a_at_t: Optional[int] = None # 사외이사 참석여부(참석(명))	예) 9,999,999,999
    od_a_at_b: Optional[int] = None # 사외이사 참석여부(불참(명))	예) 9,999,999,999
    adt_a_atn: Optional[str] = None # 감사(감사위원) 참석여부
    ftc_stt_atn: Optional[str] = None # 공정거래위원회 신고대상 여부

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "IssueIncreaseData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class ManagementProcedureData(BaseMaterialFactsData):
    """채권은행 등의 관리절차 개시"""
    mngt_pcbg_dd: Optional[str] = None # 관리절차개시 결정일자
    mngt_int: Optional[str] = None # 관리기관
    mngt_pd: Optional[str] = None # 관리기간
    mngt_rs: Optional[str] = None # 관리사유
    cfd: Optional[str] = None # 확인일자

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "ManagementProcedureData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class LegalProceedingsData(BaseMaterialFactsData):
    """소송 등의 제기"""
    icnm: Optional[str] = None # 사건의 명칭
    ac_ap: Optional[str] = None # 원고ㆍ신청인
    rq_cn: Optional[str] = None # 청구내용
    cpct: Optional[str] = None # 관할법원
    ft_ctp: Optional[str] = None # 향후대책
    lgd: Optional[str] = None # 제기일자
    cfd: Optional[str] = None # 확인일자

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "LegalProceedingsData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class ListingDecisionData(BaseMaterialFactsData):
    """해외 증권시장 주권등 상장 결정"""
    lstprstk_ostk_cnt: Optional[int] = None # 상장예정주식 종류ㆍ수(주)(보통주식)	예) 9,999,999,999
    lstprstk_estk_cnt: Optional[int] = None # 상장예정주식 종류ㆍ수(주)(기타주식)	예) 9,999,999,999
    tisstk_ostk: Optional[int] = None # 발행주식 총수(주)(보통주식)	예) 9,999,999,999
    tisstk_estk: Optional[int] = None # 발행주식 총수(주)(기타주식)	예) 9,999,999,999
    psmth_nstk_sl: Optional[int] = None # 공모방법(신주발행 (주))	예) 9,999,999,999
    psmth_ostk_sl: Optional[int] = None # 공모방법(구주매출 (주))	예) 9,999,999,999
    fdpp: Optional[str] = None # 자금조달(신주발행)
    lststk_orls: Optional[int] = None # 상장증권(원주상장 (주))	예) 9,999,999,999
    lststk_drlst: Optional[int] = None # 상장증권(DR상장 (주))	예) 9,999,999,999
    lstex_nt: Optional[str] = None # 상장거래소(소재국가)
    lstpp: Optional[str] = None # 해외상장목적
    lstprd: Optional[str] = None # 상장예정일자
    bddd: Optional[str] = None # 이사회결의일(결정일)
    od_a_at_t: Optional[int] = None # 사외이사 참석여부(참석(명))	예) 9,999,999,999
    od_a_at_b: Optional[int] = None # 사외이사 참석여부(불참(명))	예) 9,999,999,999
    adt_a_atn: Optional[str] = None # 감사(감사위원)참석여부

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "ListingDecisionData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class DelistingDecisionData(BaseMaterialFactsData):
    """해외 증권시장 주권등 상장폐지 결정"""
    dlststk_ostk_cnt: Optional[int] = None # 상장폐지주식 종류ㆍ수(주)(보통주식)	예) 9,999,999,999
    dlststk_estk_cnt: Optional[int] = None # 상장폐지주식 종류ㆍ수(주)(기타주식)	예) 9,999,999,999
    lstex_nt: Optional[str] = None # 상장거래소(소재국가)	상장거래소(소재국가)
    dlstrq_prd: Optional[str] = None # 폐지신청예정일자	폐지신청예정일자
    dlst_prd: Optional[str] = None # 폐지(예정)일자	폐지(예정)일자
    dlst_rs: Optional[str] = None # 폐지사유	폐지사유
    bddd: Optional[str] = None # 이사회결의일(확인일)	이사회결의일(확인일)
    od_a_at_t: Optional[int] = None # 사외이사 참석여부(참석(명))	예) 9,999,999,999
    od_a_at_b: Optional[int] = None # 사외이사 참석여부(불참(명))	예) 9,999,999,999
    adt_a_atn: Optional[str] = None # 감사(감사위원)참석여부

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "DelistingDecisionData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class ListingData(BaseMaterialFactsData):
    """해외 증권시장 주권등 상장"""
    lststk_ostk_cnt: Optional[int] = None # 상장주식 종류 및 수(보통주식(주))	예) 9,999,999,999
    lststk_estk_cnt: Optional[int] = None # 상장주식 종류 및 수(기타주식(주))	예) 9,999,999,999
    lstex_nt: Optional[str] = None # 상장거래소(소재국가)	상장거래소(소재국가)
    stk_cd: Optional[str] = None # 종목 명 (code)	종목 명 (code)
    lstd: Optional[str] = None # 상장일자	상장일자
    cfd: Optional[str] = None # 확인일자	확인일자

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "ListingData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class DelistingData(BaseMaterialFactsData):
    """해외 증권시장 주권등 상장폐지"""
    lstex_nt: Optional[str] = None # 상장거래소 및 소재국가
    dlststk_ostk_cnt: Optional[int] = None # 상장폐지주식의 종류(보통주식(주))	예) 9,999,999,999
    dlststk_estk_cnt: Optional[int] = None # 상장폐지주식의 종류(기타주식(주))	예) 9,999,999,999
    tredd: Optional[str] = None # 매매거래종료일
    dlst_rs: Optional[str] = None # 폐지사유
    cfd: Optional[str] = None # 확인일자

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "DelistingData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class CBIssuanceDecisionData(BaseMaterialFactsData):
    """전환사채권 발행결정"""
    bd_tm: Optional[str] = None # 사채의 종류(회차)
    bd_knd: Optional[str] = None # 사채의 종류(종류)
    bd_fta: Optional[int] = None # 사채의 권면(전자등록)총액 (원)	예) 9,999,999,999
    atcsc_rmislmt: Optional[int] = None # 정관상 잔여 발행한도 (원)	예) 9,999,999,999
    ovis_fta: Optional[int] = None # 해외발행(권면(전자등록)총액)	예) 9,999,999,999
    ovis_fta_crn: Optional[str] = None # 해외발행(권면(전자등록)총액(통화단위))
    ovis_ster: Optional[str] = None # 해외발행(기준환율등)
    ovis_isar: Optional[str] = None # 해외발행(발행지역)
    ovis_mktnm: Optional[str] = None # 해외발행(해외상장시 시장의 명칭)
    fdpp_fclt: Optional[int] = None # 자금조달의 목적(시설자금 (원))	예) 9,999,999,999
    fdpp_bsninh: Optional[int] = None # 자금조달의 목적(영업양수자금 (원))	예) 9,999,999,999
    fdpp_op: Optional[int] = None # 자금조달의 목적(운영자금 (원))	예) 9,999,999,999
    fdpp_dtrp: Optional[int] = None # 자금조달의 목적(채무상환자금 (원))	예) 9,999,999,999
    fdpp_ocsa: Optional[int] = None # 자금조달의 목적(타법인 증권 취득자금 (원))	예) 9,999,999,999
    fdpp_etc: Optional[int] = None # 자금조달의 목적(기타자금 (원))	예) 9,999,999,999
    bd_intr_ex: Optional[float] = None # 사채의 이율(표면이자율 (%))
    bd_intr_sf: Optional[float] = None # 사채의 이율(만기이자율 (%))
    bd_mtd: Optional[str] = None # 사채만기일
    bdis_mthn: Optional[str] = None # 사채발행방법
    cv_rt: Optional[float] = None # 전환에 관한 사항(전환비율 (%))
    cv_prc: Optional[int] = None # 전환에 관한 사항(전환가액 (원/주))	예) 9,999,999,999
    cvisstk_knd: Optional[str] = None # 전환에 관한 사항(전환에 따라 발행할 주식(종류))
    cvisstk_cnt: Optional[int] = None # 전환에 관한 사항(전환에 따라 발행할 주식(주식수))	예) 9,999,999,999
    cvisstk_tisstk_vs: Optional[float] = None # 전환에 관한 사항(전환에 따라 발행할 주식(주식총수 대비 비율(%)))
    cvrqpd_bgd: Optional[str] = None # 전환에 관한 사항(전환청구기간(시작일))
    cvrqpd_edd: Optional[str] = None # 전환에 관한 사항(전환청구기간(종료일))
    act_mktprcfl_cvprc_lwtrsprc: Optional[int] = None # 전환에 관한 사항(시가하락에 따른 전환가액 조정(최저 조정가액 (원)))	예) 9,999,999,999
    act_mktprcfl_cvprc_lwtrsprc_bs: Optional[str] = None # 전환에 관한 사항(시가하락에 따른 전환가액 조정(최저 조정가액 근거))
    rmislmt_lt70p: Optional[int] = None # 전환에 관한 사항(시가하락에 따른 전환가액 조정(발행당시 전환가액의 70% 미만으로 조정가능한 잔여 발행한도 (원)))	예) 9,999,999,999
    abmg: Optional[str] = None # 합병 관련 사항
    sbd: Optional[str] = None # 청약일	청약일
    pymd: Optional[str] = None # 납입일	납입일
    rpmcmp: Optional[str] = None # 대표주관회사	대표주관회사
    grint: Optional[str] = None # 보증기관	보증기관
    bddd: Optional[str] = None # 이사회결의일(결정일)	이사회결의일(결정일)
    od_a_at_t: Optional[int] = None # 사외이사 참석여부(참석 (명))	예) 9,999,999,999
    od_a_at_b: Optional[int] = None # 사외이사 참석여부(불참 (명))	예) 9,999,999,999
    adt_a_atn: Optional[str] = None # 감사(감사위원) 참석여부	감사(감사위원) 참석여부
    rs_sm_atn: Optional[str] = None # 증권신고서 제출대상 여부	증권신고서 제출대상 여부
    ex_sm_r: Optional[str] = None # 제출을 면제받은 경우 그 사유	제출을 면제받은 경우 그 사유
    ovis_ltdtl: Optional[str] = None # 당해 사채의 해외발행과 연계된 대차거래 내역	당해 사채의 해외발행과 연계된 대차거래 내역
    ftc_stt_atn: Optional[str] = None # 공정거래위원회 신고대상 여부

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "CBIssuanceDecisionData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class BWIssuanceDecisionData(BaseMaterialFactsData):
    """신주인수권부사채권 발행결정"""
    bd_tm: Optional[str] = None # 사채의 종류(회차)
    bd_knd: Optional[str] = None # 사채의 종류(종류)
    bd_fta: Optional[int] = None # 사채의 권면(전자등록)총액 (원)	예) 9,999,999,999
    atcsc_rmislmt: Optional[int] = None # 정관상 잔여 발행한도 (원)	예) 9,999,999,999
    ovis_fta: Optional[int] = None # 해외발행(권면(전자등록)총액)	예) 9,999,999,999
    ovis_fta_crn: Optional[str] = None # 해외발행(권면(전자등록)총액(통화단위))
    ovis_ster: Optional[str] = None # 해외발행(기준환율등)
    ovis_isar: Optional[str] = None # 해외발행(발행지역)
    ovis_mktnm: Optional[str] = None # 해외발행(해외상장시 시장의 명칭)
    fdpp_fclt: Optional[int] = None # 자금조달의 목적(시설자금 (원))	예) 9,999,999,999
    fdpp_bsninh: Optional[int] = None # 자금조달의 목적(영업양수자금 (원))	예) 9,999,999,999
    fdpp_op: Optional[int] = None # 자금조달의 목적(운영자금 (원))	예) 9,999,999,999
    fdpp_dtrp: Optional[int] = None # 자금조달의 목적(채무상환자금 (원))	예) 9,999,999,999
    fdpp_ocsa: Optional[int] = None # 자금조달의 목적(타법인 증권 취득자금 (원))	예) 9,999,999,999
    fdpp_etc: Optional[int] = None # 자금조달의 목적(기타자금 (원))	예) 9,999,999,999
    bd_intr_ex: Optional[float] = None # 사채의 이율(표면이자율 (%))
    bd_intr_sf: Optional[float] = None # 사채의 이율(만기이자율 (%))
    bd_mtd: Optional[str] = None # 사채만기일
    bdis_mthn: Optional[str] = None # 사채발행방법
    ex_rt: Optional[float] = None # 신주인수권에 관한 사항(행사비율 (%))
    ex_prc: Optional[int] = None # 신주인수권에 관한 사항(행사가액 (원/주))	예) 9,999,999,999
    ex_prc_dmth: Optional[str] = None # 신주인수권에 관한 사항(행사가액 결정방법)
    bdwt_div_atn: Optional[str] = None # 신주인수권에 관한 사항(사채와 인수권의 분리여부)
    nstk_pym_mth: Optional[str] = None # 신주인수권에 관한 사항(신주대금 납입방법)
    nstk_isstk_knd: Optional[str] = None # 신주인수권에 관한 사항(신주인수권 행사에 따라 발행할 주식(종류))
    nstk_isstk_cnt: Optional[int] = None # 신주인수권에 관한 사항(신주인수권 행사에 따라 발행할 주식(주식수))	예) 9,999,999,999
    nstk_isstk_tisstk_vs: Optional[float] = None # 신주인수권에 관한 사항(신주인수권 행사에 따라 발행할 주식(주식총수 대비 비율(%)))
    expd_bgd: Optional[str] = None # 신주인수권에 관한 사항(권리행사기간(시작일))
    expd_edd: Optional[str] = None # 신주인수권에 관한 사항(권리행사기간(종료일))
    act_mktprcfl_cvprc_lwtrsprc: Optional[int] = None # 신주인수권에 관한 사항(시가하락에 따른 행사가액 조정(최저 조정가액 (원)))	예) 9,999,999,999
    act_mktprcfl_cvprc_lwtrsprc_bs: Optional[str] = None # 신주인수권에 관한 사항(시가하락에 따른 행사가액 조정(최저 조정가액 근거))
    rmislmt_lt70p: Optional[int] = None # 신주인수권에 관한 사항(시가하락에 따른 행사가액 조정(발행당시 행사가액의 70% 미만으로 조정가능한 잔여 발행한도 (원)))	예) 9,999,999,999
    abmg: Optional[str] = None # 합병 관련 사항
    sbd: Optional[str] = None # 청약일
    pymd: Optional[str] = None # 납입일
    rpmcmp: Optional[str] = None # 대표주관회사
    grint: Optional[str] = None # 보증기관
    bddd: Optional[str] = None # 이사회결의일(결정일)
    od_a_at_t: Optional[int] = None # 사외이사 참석여부(참석 (명))	예) 9,999,999,999
    od_a_at_b: Optional[int] = None # 사외이사 참석여부(불참 (명))	예) 9,999,999,999
    adt_a_atn: Optional[str] = None # 감사(감사위원) 참석여부
    rs_sm_atn: Optional[str] = None # 증권신고서 제출대상 여부
    ex_sm_r: Optional[str] = None # 제출을 면제받은 경우 그 사유
    ovis_ltdtl: Optional[str] = None # 당해 사채의 해외발행과 연계된 대차거래 내역
    ftc_stt_atn: Optional[str] = None # 공정거래위원회 신고대상 여부

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "BWIssuanceDecisionData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class EBIssuanceDecisionData(BaseMaterialFactsData):
    """교환사채권 발행결정"""
    bd_tm: Optional[str] = None # 사채의 종류(회차)
    bd_knd: Optional[str] = None # 사채의 종류(종류)
    bd_fta: Optional[int] = None # 사채의 권면(전자등록)총액 (원)	예) 9,999,999,999
    ovis_fta: Optional[int] = None # 해외발행(권면(전자등록)총액)	예) 9,999,999,999
    ovis_fta_crn: Optional[str] = None # 해외발행(권면(전자등록)총액(통화단위))
    ovis_ster: Optional[str] = None # 해외발행(기준환율등)
    ovis_isar: Optional[str] = None # 해외발행(발행지역)
    ovis_mktnm: Optional[str] = None # 해외발행(해외상장시 시장의 명칭)
    fdpp_fclt: Optional[int] = None # 자금조달의 목적(시설자금 (원))	예) 9,999,999,999
    fdpp_bsninh: Optional[int] = None # 자금조달의 목적(영업양수자금 (원))	예) 9,999,999,999
    fdpp_op: Optional[int] = None # 자금조달의 목적(운영자금 (원))	예) 9,999,999,999
    fdpp_dtrp: Optional[int] = None # 자금조달의 목적(채무상환자금 (원))	예) 9,999,999,999
    fdpp_ocsa: Optional[int] = None # 자금조달의 목적(타법인 증권 취득자금 (원))	예) 9,999,999,999
    fdpp_etc: Optional[int] = None # 자금조달의 목적(기타자금 (원))	예) 9,999,999,999
    bd_intr_ex: Optional[float] = None # 사채의 이율(표면이자율 (%))
    bd_intr_sf: Optional[float] = None # 사채의 이율(만기이자율 (%))
    bd_mtd: Optional[str] = None # 사채만기일
    bdis_mthn: Optional[str] = None # 사채발행방법
    ex_rt: Optional[float] = None # 교환에 관한 사항(교환비율 (%))
    ex_prc: Optional[int] = None # 교환에 관한 사항(교환가액 (원/주))	예) 9,999,999,999
    ex_prc_dmth: Optional[str] = None # 교환에 관한 사항(교환가액 결정방법)
    extg: Optional[str] = None # 교환에 관한 사항(교환대상(종류))
    extg_stkcnt: Optional[int] = None # 교환에 관한 사항(교환대상(주식수))	예) 9,999,999,999
    extg_tisstk_vs: Optional[float] = None # 교환에 관한 사항(교환대상(주식총수 대비 비율(%)))
    exrqpd_bgd: Optional[str] = None # 교환에 관한 사항(교환청구기간(시작일))
    exrqpd_edd: Optional[str] = None # 교환에 관한 사항(교환청구기간(종료일))
    sbd: Optional[str] = None # 청약일
    pymd: Optional[str] = None # 납입일
    rpmcmp: Optional[str] = None # 대표주관회사
    grint: Optional[str] = None # 보증기관
    bddd: Optional[str] = None # 이사회결의일(결정일)
    od_a_at_t: Optional[int] = None # 사외이사 참석여부(참석 (명))	예) 9,999,999,999
    od_a_at_b: Optional[int] = None # 사외이사 참석여부(불참 (명))	예) 9,999,999,999
    adt_a_atn: Optional[str] = None # 감사(감사위원) 참석여부
    rs_sm_atn: Optional[str] = None # 증권신고서 제출대상 여부
    ex_sm_r: Optional[str] = None # 제출을 면제받은 경우 그 사유
    ovis_ltdtl: Optional[str] = None # 당해 사채의 해외발행과 연계된 대차거래 내역
    ftc_stt_atn: Optional[str] = None # 공정거래위원회 신고대상 여부

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "ExchangeBondIssuanceDecisionData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class CreditorBankManagementProcessSuspensionData(BaseMaterialFactsData):
    """채권은행 등의 관리절차 중단"""
    mngt_pcsp_dd: Optional[str] = None # 관리절차중단 결정일자
    mngt_int: Optional[str] = None # 관리기관
    sp_rs: Optional[str] = None # 중단사유
    ft_ctp: Optional[str] = None # 향후대책
    cfd: Optional[str] = None # 확인일자

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "CreditorBankManagementProcessSuspensionData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class CoCoBondIssuanceDecisionData(BaseMaterialFactsData):
    """상각형 조건부자본증권 발행결정"""
    bd_tm: Optional[str] = None # 사채의 종류(회차)
    bd_knd: Optional[str] = None # 사채의 종류(종류)
    bd_fta: Optional[int] = None # 사채의 권면(전자등록)총액 (원)	예) 9,999,999,999
    ovis_fta: Optional[int] = None # 해외발행(권면(전자등록)총액)	예) 9,999,999,999
    ovis_fta_crn: Optional[str] = None # 해외발행(권면(전자등록)총액(통화단위))
    ovis_ster: Optional[str] = None # 해외발행(기준환율등)
    ovis_isar: Optional[str] = None # 해외발행(발행지역)
    ovis_mktnm: Optional[str] = None # 해외발행(해외상장시 시장의 명칭)
    fdpp_fclt: Optional[int] = None # 자금조달의 목적(시설자금 (원))	예) 9,999,999,999
    fdpp_bsninh: Optional[int] = None # 자금조달의 목적(영업양수자금 (원))	예) 9,999,999,999
    fdpp_op: Optional[int] = None # 자금조달의 목적(운영자금 (원))	예) 9,999,999,999
    fdpp_dtrp: Optional[int] = None # 자금조달의 목적(채무상환자금 (원))	예) 9,999,999,999
    fdpp_ocsa: Optional[int] = None # 자금조달의 목적(타법인 증권 취득자금 (원))	예) 9,999,999,999
    fdpp_etc: Optional[int] = None # 자금조달의 목적(기타자금 (원))	예) 9,999,999,999
    bd_intr_sf: Optional[float] = None # 사채의 이율(표면이자율 (%))
    bd_intr_ex: Optional[float] = None # 사채의 이율(만기이자율 (%))
    bd_mtd: Optional[str] = None # 사채만기일
    dbtrs_sc: Optional[str] = None # 채무재조정에 관한 사항(채무재조정의 범위)
    sbd: Optional[str] = None # 청약일
    pymd: Optional[str] = None # 납입일
    rpmcmp: Optional[str] = None # 대표주관회사
    grint: Optional[str] = None # 보증기관
    bddd: Optional[str] = None # 이사회결의일(결정일)
    od_a_at_t: Optional[int] = None # 사외이사 참석여부(참석 (명))	예) 9,999,999,999
    od_a_at_b: Optional[int] = None # 사외이사 참석여부(불참 (명))	예) 9,999,999,999
    adt_a_atn: Optional[str] = None # 감사(감사위원) 참석여부
    rs_sm_atn: Optional[str] = None # 증권신고서 제출대상 여부
    ex_sm_r: Optional[str] = None # 제출을 면제받은 경우 그 사유
    ovis_ltdtl: Optional[str] = None # 당해 사채의 해외발행과 연계된 대차거래 내역
    ftc_stt_atn: Optional[str] = None # 공정거래위원회 신고대상 여부

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "CoCoBondIssuanceDecisionData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class ShareBuybackDecisionData(BaseMaterialFactsData):
    """자기주식 취득 결정"""
    aqpln_stk_ostk: Optional[int] = None # 취득예정주식(주)(보통주식)	9,999,999,999
    aqpln_stk_estk: Optional[int] = None # 취득예정주식(주)(기타주식)	9,999,999,999
    aqpln_prc_ostk: Optional[int] = None # 취득예정금액(원)(보통주식)	9,999,999,999
    aqpln_prc_estk: Optional[int] = None # 취득예정금액(원)(기타주식)	9,999,999,999
    aqexpd_bgd: Optional[str] = None # 취득예상기간(시작일)
    aqexpd_edd: Optional[str] = None # 취득예상기간(종료일)
    hdexpd_bgd: Optional[str] = None # 보유예상기간(시작일)
    hdexpd_edd: Optional[str] = None # 보유예상기간(종료일)
    aq_pp: Optional[str] = None # 취득목적
    aq_mth: Optional[str] = None # 취득방법
    cs_iv_bk: Optional[str] = None # 위탁투자중개업자
    aq_wtn_div_ostk: Optional[int] = None # 취득 전 자기주식 보유현황(배당가능이익 범위 내 취득(주)(보통주식))	9,999,999,999
    aq_wtn_div_ostk_rt: Optional[float] = None # 취득 전 자기주식 보유현황(배당가능이익 범위 내 취득(주)(비율(%)))
    aq_wtn_div_estk: Optional[int] = None # 취득 전 자기주식 보유현황(배당가능이익 범위 내 취득(주)(기타주식))	9,999,999,999
    aq_wtn_div_estk_rt: Optional[float] = None # 취득 전 자기주식 보유현황(배당가능이익 범위 내 취득(주)(비율(%)))
    eaq_ostk: Optional[int] = None # 취득 전 자기주식 보유현황(기타취득(주)(보통주식))	9,999,999,999
    eaq_ostk_rt: Optional[float] = None # 취득 전 자기주식 보유현황(기타취득(주)(비율(%)))
    eaq_estk: Optional[int] = None # 취득 전 자기주식 보유현황(기타취득(주)(기타주식))	9,999,999,999
    eaq_estk_rt: Optional[float] = None # 취득 전 자기주식 보유현황(기타취득(주)(비율(%)))
    aq_dd: Optional[str] = None # 취득결정일
    od_a_at_t: Optional[int] = None # 사외이사참석여부(참석(명))	9,999,999,999
    od_a_at_b: Optional[int] = None # 사외이사참석여부(불참(명))	9,999,999,999
    adt_a_atn: Optional[str] = None # 감사(사외이사가 아닌 감사위원)참석여부
    d1_prodlm_ostk: Optional[int] = None # 1일 매수 주문수량 한도(보통주식)	9,999,999,999
    d1_prodlm_estk: Optional[int] = None # 1일 매수 주문수량 한도(기타주식)	9,999,999,999

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "ShareBuybackDecisionData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class TreasuryStockDisposalDecisionData(BaseMaterialFactsData):
    """자기주식 처분 결정"""
    dppln_stk_ostk: Optional[int] = None # 처분예정주식(주)(보통주식)	9,999,999,999
    dppln_stk_estk: Optional[int] = None # 처분예정주식(주)(기타주식)	9,999,999,999
    dpstk_prc_ostk: Optional[int] = None # 처분 대상 주식가격(원)(보통주식)	9,999,999,999
    dpstk_prc_estk: Optional[int] = None # 처분 대상 주식가격(원)(기타주식)	9,999,999,999
    dppln_prc_ostk: Optional[int] = None # 처분예정금액(원)(보통주식)	9,999,999,999
    dppln_prc_estk: Optional[int] = None # 처분예정금액(원)(기타주식)	9,999,999,999
    dpprpd_bgd: Optional[str] = None #처분예정기간(시작일)
    dpprpd_edd: Optional[str] = None #처분예정기간(종료일)
    dp_pp: Optional[str] = None #처분목적
    dp_m_mkt: Optional[int] = None # 처분방법(시장을 통한 매도(주))	9,999,999,999
    dp_m_ovtm: Optional[int] = None # 처분방법(시간외대량매매(주))	9,999,999,999
    dp_m_otc: Optional[int] = None # 처분방법(장외처분(주))	9,999,999,999
    dp_m_etc: Optional[int] = None # 처분방법(기타(주))	9,999,999,999
    cs_iv_bk: Optional[str] = None #위탁투자중개업자
    aq_wtn_div_ostk: Optional[int] = None # 처분 전 자기주식 보유현황(배당가능이익 범위 내 취득(주)(보통주식))	9,999,999,999
    aq_wtn_div_ostk_rt: Optional[float] = None # 처분 전 자기주식 보유현황(배당가능이익 범위 내 취득(주)(비율(%)))
    aq_wtn_div_estk: Optional[int] = None # 처분 전 자기주식 보유현황(배당가능이익 범위 내 취득(주)(기타주식))	9,999,999,999
    aq_wtn_div_estk_rt: Optional[float] = None # 처분 전 자기주식 보유현황(배당가능이익 범위 내 취득(주)(비율(%)))
    eaq_ostk: Optional[int] = None # 처분 전 자기주식 보유현황(기타취득(주)(보통주식))	9,999,999,999
    eaq_ostk_rt: Optional[float] = None # 처분 전 자기주식 보유현황(기타취득(주)(비율(%)))
    eaq_estk: Optional[int] = None # 처분 전 자기주식 보유현황(기타취득(주)(기타주식))	9,999,999,999
    eaq_estk_rt: Optional[float] = None # 처분 전 자기주식 보유현황(기타취득(주)(비율(%)))
    dp_dd: Optional[str] = None #처분결정일
    od_a_at_t: Optional[int] = None # 사외이사참석여부(참석(명))	9,999,999,999
    od_a_at_b: Optional[int] = None # 사외이사참석여부(불참(명))	9,999,999,999
    adt_a_atn: Optional[str] = None #감사(사외이사가 아닌 감사위원)참석여부
    d1_slodlm_ostk: Optional[int] = None # 1일 매도 주문수량 한도(보통주식)	9,999,999,999
    d1_slodlm_estk: Optional[int] = None # 1일 매도 주문수량 한도(기타주식)	9,999,999,999

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "TreasuryStockDisposalDecisionData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class TrustAgreementAcquisitionDecisionData(BaseMaterialFactsData):
    """자기주식취득 신탁계약 체결 결정"""
    ctr_prc: Optional[int] = None # 계약금액(원)	9,999,999,999
    ctr_pd_bgd: Optional[str] = None # 계약기간(시작일)
    ctr_pd_edd: Optional[str] = None # 계약기간(종료일)
    ctr_pp: Optional[str] = None # 계약목적
    ctr_cns_int: Optional[str] = None # 계약체결기관
    ctr_cns_prd: Optional[str] = None # 계약체결 예정일자
    aq_wtn_div_ostk: Optional[int] = None # 계약 전 자기주식 보유현황(배당가능범위 내 취득(주)(보통주식))	9,999,999,999
    aq_wtn_div_ostk_rt: Optional[float] = None # 계약 전 자기주식 보유현황(배당가능범위 내 취득(주)(비율(%)))
    aq_wtn_div_estk: Optional[int] = None # 계약 전 자기주식 보유현황(배당가능범위 내 취득(주)(기타주식))	9,999,999,999
    aq_wtn_div_estk_rt: Optional[float] = None # 계약 전 자기주식 보유현황(배당가능범위 내 취득(주)(비율(%)))
    eaq_ostk: Optional[int] = None # 계약 전 자기주식 보유현황(기타취득(주)(보통주식))	9,999,999,999
    eaq_ostk_rt: Optional[float] = None # 계약 전 자기주식 보유현황(기타취득(주)(비율(%)))
    eaq_estk: Optional[int] = None # 계약 전 자기주식 보유현황(기타취득(주)(기타주식))	9,999,999,999
    eaq_estk_rt: Optional[float] = None # 계약 전 자기주식 보유현황(기타취득(주)(비율(%)))
    bddd: Optional[str] = None # 이사회결의일(결정일)
    od_a_at_t: Optional[int] = None # 사외이사참석여부(참석(명))	9,999,999,999
    od_a_at_b: Optional[int] = None # 사외이사참석여부(불참(명))	9,999,999,999
    adt_a_atn: Optional[str] = None # 감사(사외이사가 아닌 감사위원)참석여부
    cs_iv_bk: Optional[str] = None # 위탁투자중개업자

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "TrustAgreementAcquisitionDecisionData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class TrustAgreementResolutionDecisionData(BaseMaterialFactsData):
    """자기주식취득 신탁계약 해지 결정"""
    ctr_prc_bfcc: Optional[int] = None # 계약금액(원)(해지 전)	9,999,999,999
    ctr_prc_atcc: Optional[int] = None # 계약금액(원)(해지 후)	9,999,999,999
    ctr_pd_bfcc_bgd: Optional[str] = None # 해지 전 계약기간(시작일)
    ctr_pd_bfcc_edd: Optional[str] = None # 해지 전 계약기간(종료일)
    cc_pp: Optional[str] = None # 해지목적
    cc_int: Optional[str] = None # 해지기관
    cc_prd: Optional[str] = None # 해지예정일자
    tp_rm_atcc: Optional[str] = None # 해지후 신탁재산의 반환방법
    aq_wtn_div_ostk: Optional[int] = None # 해지 전 자기주식 보유현황(배당가능범위 내 취득(주)(보통주식))	9,999,999,999
    aq_wtn_div_ostk_rt: Optional[float] = None # 해지 전 자기주식 보유현황(배당가능범위 내 취득(주)(비율(%)))
    aq_wtn_div_estk: Optional[int] = None # 해지 전 자기주식 보유현황(배당가능범위 내 취득(주)(기타주식))	9,999,999,999
    aq_wtn_div_estk_rt: Optional[float] = None # 해지 전 자기주식 보유현황(배당가능범위 내 취득(주)(비율(%)))
    eaq_ostk: Optional[int] = None # 해지 전 자기주식 보유현황(기타취득(주)(보통주식))	9,999,999,999
    eaq_ostk_rt: Optional[float] = None # 해지 전 자기주식 보유현황(기타취득(주)(비율(%)))
    eaq_estk: Optional[int] = None # 해지 전 자기주식 보유현황(기타취득(주)(기타주식))	9,999,999,999
    eaq_estk_rt: Optional[float] = None # 해지 전 자기주식 보유현황(기타취득(주)(비율(%)))
    bddd: Optional[str] = None # 이사회결의일(결정일)
    od_a_at_t: Optional[int] = None # 사외이사참석여부(참석(명))	9,999,999,999
    od_a_at_b: Optional[int] = None # 사외이사참석여부(불참(명))	9,999,999,999
    adt_a_atn: Optional[str] = None # 감사(사외이사가 아닌 감사위원)참석여부

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "TrustAgreementResolutionDecisionData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class BusinessAcquisitionDecisionData(BaseMaterialFactsData):
    """영업양수 결정"""
    inh_bsn: Optional[str] = None # 양수영업
    inh_bsn_mc: Optional[str] = None # 양수영업 주요내용
    inh_prc: Optional[int] = None # 양수가액(원)	9,999,999,999
    absn_inh_atn: Optional[str] = None # 영업전부의 양수 여부
    ast_inh_bsn: Optional[int] = None # 재무내용(원)(자산액(양수대상 영업부문(A)))	9,999,999,999
    ast_cmp_all: Optional[int] = None # 재무내용(원)(자산액(당사전체(B)))	9,999,999,999
    ast_rt: Optional[float] = None # 재무내용(원)(자산액(비중(%)(A/B))
    sl_inh_bsn: Optional[int] = None # 재무내용(원)(매출액(양수대상 영업부문(A)))	9,999,999,999
    sl_cmp_all: Optional[int] = None # 재무내용(원)(매출액(당사전체(B)))	9,999,999,999
    sl_rt: Optional[float] = None # 재무내용(원)(매출액(비중(%)(A/B)))
    dbt_inh_bsn: Optional[int] = None # 재무내용(원)(부채액(양수대상 영업부문(A)))	9,999,999,999
    dbt_cmp_all: Optional[int] = None # 재무내용(원)(부채액(당사전체(B)))	9,999,999,999
    dbt_rt: Optional[float] = None # 재무내용(원)(부채액(비중(%)(A/B)))
    inh_pp: Optional[str] = None # 양수목적
    inh_af: Optional[str] = None # 양수영향
    inh_prd_ctr_cnsd: Optional[str] = None # 양수예정일자(계약체결일)
    inh_prd_inh_std: Optional[str] = None # 양수예정일자(양수기준일)
    dlptn_cmpnm: Optional[str] = None # 거래상대방(회사명(성명))
    dlptn_cpt: Optional[int] = None # 거래상대방(자본금(원))	9,999,999,999
    dlptn_mbsn: Optional[str] = None # 거래상대방(주요사업)
    dlptn_hoadd: Optional[str] = None # 거래상대방(본점소재지(주소))
    dlptn_rl_cmpn: Optional[str] = None # 거래상대방(회사와의 관계)
    inh_pym: Optional[str] = None # 양수대금지급
    exevl_atn: Optional[str] = None # 외부평가에 관한 사항(외부평가 여부)
    exevl_bs_rs: Optional[str] = None # 외부평가에 관한 사항(근거 및 사유)
    exevl_intn: Optional[str] = None # 외부평가에 관한 사항(외부평가기관의 명칭)
    exevl_pd: Optional[str] = None # 외부평가에 관한 사항(외부평가 기간)
    exevl_op: Optional[str] = None # 외부평가에 관한 사항(외부평가 의견)
    gmtsck_spd_atn: Optional[str] = None # 주주총회 특별결의 여부
    gmtsck_prd: Optional[str] = None # 주주총회 예정일자
    aprskh_plnprc: Optional[int] = None # 주식매수청구권에 관한 사항(매수예정가격)	9,999,999,999
    aprskh_pym_plpd_mth: Optional[str] = None # 주식매수청구권에 관한 사항(지급예정시기, 지급방법)
    aprskh_lmt: Optional[str] = None # 주식매수청구권에 관한 사항(주식매수청구권 제한 관련 내용)
    aprskh_ctref: Optional[str] = None # 주식매수청구권에 관한 사항(계약에 미치는 효력)
    bddd: Optional[str] = None # 이사회결의일(결정일)
    od_a_at_t: Optional[int] = None # 사외이사참석여부(참석(명))	9,999,999,999
    od_a_at_b: Optional[int] = None # 사외이사참석여부(불참(명))	9,999,999,999
    adt_a_atn: Optional[str] = None # 감사(사외이사가 아닌 감사위원) 참석여부
    bdlst_atn: Optional[str] = None # 우회상장 해당 여부
    n6m_tpai_plann: Optional[str] = None # 향후 6월이내 제3자배정 증자 등 계획
    otcpr_bdlst_sf_atn: Optional[str] = None # 타법인의 우회상장 요건 충족여부
    ftc_stt_atn: Optional[str] = None # 공정거래위원회 신고대상 여부
    popt_ctr_atn: Optional[str] = None # 풋옵션 등 계약 체결여부
    popt_ctr_cn: Optional[str] = None # 계약내용

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "BusinessAcquisitionDecisionData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class BusinessTransferDecisionData(BaseMaterialFactsData):
    """영업양도 결정"""
    trf_bsn: Optional[str] = None # 양도영업
    trf_bsn_mc: Optional[str] = None # 양도영업 주요내용
    trf_prc: Optional[int] = None # 양도가액(원)) 예) 9,999,999,999
    ast_trf_bsn: Optional[int] = None # 재무내용(원)(자산액(양도대상 영업부문(A))) 예) 9,999,999,999
    ast_cmp_all: Optional[int] = None # 재무내용(원)(자산액(당사전체(B)))) 예) 9,999,999,999
    ast_rt: Optional[float] = None # 재무내용(원)(자산액(비중(%)(A/B)))
    sl_trf_bsn: Optional[int] = None # 재무내용(원)(매출액(양도대상 영업부문(A)))) 예) 9,999,999,999
    sl_cmp_all: Optional[int] = None # 재무내용(원)(매출액(당사전체(B)))) 예) 9,999,999,999
    sl_rt: Optional[float] = None # 재무내용(원)(매출액(비중(%)(A/B)))
    trf_pp: Optional[str] = None # 양도목적
    trf_af: Optional[str] = None # 양도영향
    trf_prd_ctr_cnsd: Optional[str] = None # 양도예정일자(계약체결일)
    trf_prd_trf_std: Optional[str] = None # 양도예정일자(양도기준일)
    dlptn_cmpnm: Optional[str] = None # 거래상대방(회사명(성명))
    dlptn_cpt: Optional[int] = None # 거래상대방(자본금(원)) 예) 9,999,999,999
    dlptn_mbsn: Optional[str] = None # 거래상대방(주요사업)
    dlptn_hoadd: Optional[str] = None # 거래상대방(본점소재지(주소))
    dlptn_rl_cmpn: Optional[str] = None # 거래상대방(회사와의 관계)
    trf_pym: Optional[int] = None # 양도대금지급
    exevl_atn: Optional[str] = None # 외부평가에 관한 사항(외부평가 여부)
    exevl_bs_rs: Optional[str] = None # 외부평가에 관한 사항(근거 및 사유)
    exevl_intn: Optional[str] = None # 외부평가에 관한 사항(외부평가기관의 명칭)
    exevl_pd: Optional[str] = None # 외부평가에 관한 사항(외부평가 기간)
    exevl_op: Optional[str] = None # 외부평가에 관한 사항(외부평가 의견)
    gmtsck_spd_atn: Optional[str] = None # 주주총회 특별결의 여부
    gmtsck_prd: Optional[str] = None # 주주총회 예정일자
    aprskh_plnprc: Optional[int] = None # 주식매수청구권에 관한 사항(매수예정가격) 예) 9,999,999,999
    aprskh_pym_plpd_mth: Optional[str] = None # 주식매수청구권에 관한 사항(지급예정시기, 지급방법)
    aprskh_lmt: Optional[str] = None # 주식매수청구권에 관한 사항(주식매수청구권 제한 관련 내용)
    aprskh_ctref: Optional[str] = None # 주식매수청구권에 관한 사항(계약에 미치는 효력)
    bddd: Optional[str] = None # 이사회결의일(결정일)
    od_a_at_t: Optional[int] = None # 사외이사참석여부(참석(명)) 예) 9,999,999,999
    od_a_at_b: Optional[int] = None # 사외이사참석여부(불참(명)) 예) 9,999,999,999
    adt_a_atn: Optional[str] = None # 감사(사외이사가 아닌 감사위원) 참석여부
    ftc_stt_atn: Optional[str] = None # 공정거래위원회 신고대상 여부
    popt_ctr_atn: Optional[str] = None # 풋옵션 등 계약 체결여부
    popt_ctr_cn: Optional[str] = None # 계약내용

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "BusinessTransferDecisionData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class AssetTransferDecisionData(BaseMaterialFactsData):
    """유형자산 양수/양도 결정"""
    ast_sen: Optional[str] = None # 자산구분
    ast_nm: Optional[str] = None # 자산명

    # 양수
    inhdtl_inhprc: Optional[int] = None # 양수내역(양수금액(원)) 예) 9,999,999,999
    inhdtl_tast: Optional[int] = None # 양수내역(자산총액(원)) 예) 9,999,999,999
    inhdtl_tast_vs: Optional[float] = None # 양수내역(자산총액대비(%))
    inh_pp: Optional[str] = None # 양수목적
    inh_af: Optional[str] = None # 양수영향
    inh_prd_ctr_cnsd: Optional[str] = None # 양수예정일자(계약체결일)
    inh_prd_inh_std: Optional[str] = None # 양수예정일자(양수기준일)
    inh_prd_rgs_prd: Optional[str] = None # 양수예정일자(등기예정일)

    # 양도
    trfdtl_trfprc: Optional[int] = None # 양도내역(양도금액(원)) 예) 9,999,999,999
    trfdtl_tast: Optional[int] = None # 양도내역(자산총액(원)) 예) 9,999,999,999
    trfdtl_tast_vs: Optional[float] = None # 양도내역(자산총액대비(%))
    trf_pp: Optional[str] = None # 양도목적
    trf_af: Optional[str] = None # 양도영향
    trf_prd_ctr_cnsd: Optional[str] = None # 양도예정일자(계약체결일)
    trf_prd_trf_std: Optional[str] = None # 양도예정일자(양도기준일)
    trf_prd_rgs_prd: Optional[str] = None # 양도예정일자(등기예정일)

    dlptn_cmpnm: Optional[str] = None # 거래상대방(회사명(성명))
    dlptn_cpt: Optional[int] = None # 거래상대방(자본금(원)) 예) 9,999,999,999
    dlptn_mbsn: Optional[str] = None # 거래상대방(주요사업)
    dlptn_hoadd: Optional[str] = None # 거래상대방(본점소재지(주소))
    dlptn_rl_cmpn: Optional[str] = None # 거래상대방(회사와의 관계)
    dl_pym: Optional[int] = None # 거래대금지급
    exevl_atn: Optional[str] = None # 외부평가에 관한 사항(외부평가 여부)
    exevl_bs_rs: Optional[str] = None # 외부평가에 관한 사항(근거 및 사유)
    exevl_intn: Optional[str] = None # 외부평가에 관한 사항(외부평가기관의 명칭)
    exevl_pd: Optional[str] = None # 외부평가에 관한 사항(외부평가 기간)
    exevl_op: Optional[str] = None # 외부평가에 관한 사항(외부평가 의견)
    gmtsck_spd_atn: Optional[str] = None # 주주총회 특별결의 여부
    gmtsck_prd: Optional[str] = None # 주주총회 예정일자
    aprskh_exrq: Optional[str] = None # 주식매수청구권에 관한 사항(행사요건)
    aprskh_plnprc: Optional[int] = None # 주식매수청구권에 관한 사항(매수예정가격) 예) 9,999,999,999
    aprskh_ex_pc_mth_pd_pl: Optional[str] = None # 주식매수청구권에 관한 사항(행사절차, 방법, 기간, 장소)
    aprskh_pym_plpd_mth: Optional[str] = None # 주식매수청구권에 관한 사항(지급예정시기, 지급방법)
    aprskh_lmt: Optional[str] = None # 주식매수청구권에 관한 사항(주식매수청구권 제한 관련 내용)
    aprskh_ctref: Optional[str] = None # 주식매수청구권에 관한 사항(계약에 미치는 효력)
    bddd: Optional[str] = None # 이사회결의일(결정일)
    od_a_at_t: Optional[int] = None # 사외이사참석여부(참석(명)) 예) 9,999,999,999
    od_a_at_b: Optional[int] = None # 사외이사참석여부(불참(명)) 예) 9,999,999,999
    adt_a_atn: Optional[str] = None # 감사(사외이사가 아닌 감사위원) 참석여부
    ftc_stt_atn: Optional[str] = None # 공정거래위원회 신고대상 여부
    popt_ctr_atn: Optional[str] = None # 풋옵션 등 계약 체결여부
    popt_ctr_cn: Optional[str] = None # 계약내용

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "AssetTransferDecisionData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class OtherShareTransferDecisionData(BaseMaterialFactsData):
    """타법인 주식 및 출자증권 양수/얃도 결정"""
    iscmp_cmpnm: Optional[str] = None # 발행회사(회사명)
    iscmp_nt: Optional[str] = None # 발행회사(국적)
    iscmp_rp: Optional[str] = None # 발행회사(대표자)
    iscmp_cpt: Optional[int] = None # 발행회사(자본금(원)) 예) 9,999,999,999
    iscmp_rl_cmpn: Optional[str] = None # 발행회사(회사와 관계)
    iscmp_tisstk: Optional[int] = None # 발행회사(발행주식 총수(주)) 예) 9,999,999,999
    iscmp_mbsn: Optional[str] = None # 발행회사(주요사업)
    l6m_tpa_nstkaq_atn: Optional[str] = None # 최근 6월 이내 제3자 배정에 의한 신주취득 여부

    inhdtl_stkcnt: Optional[int] = None # 양수내역(양수주식수(주)) 예) 9,999,999,999
    inhdtl_inhprc: Optional[int] = None # 양수내역(양수금액(원)(A)) 예) 9,999,999,999
    inhdtl_tast: Optional[int] = None # 양수내역(총자산(원)(B)) 예) 9,999,999,999
    inhdtl_tast_vs: Optional[float] = None # 양수내역(총자산대비(%)(A/B))
    inhdtl_ecpt: Optional[int] = None # 양수내역(자기자본(원)(C)) 예) 9,999,999,999
    inhdtl_ecpt_vs: Optional[float] = None # 양수내역(자기자본대비(%)(A/C))
    atinh_owstkcnt: Optional[int] = None # 양수후 소유주식수 및 지분비율(소유주식수(주)) 예) 9,999,999,999
    atinh_eqrt: Optional[float] = None # 양수후 소유주식수 및 지분비율(지분비율(%))
    inh_pp: Optional[str] = None # 양수목적
    inh_prd: Optional[str] = None # 양수예정일자

    trfdtl_stkcnt: Optional[int] = None # 양도내역(양도주식수(주)) 예) 9,999,999,999
    trfdtl_trfprc: Optional[int] = None # 양도내역(양도금액(원)(A)) 예) 9,999,999,999
    trfdtl_tast: Optional[int] = None # 양도내역(총자산(원)(B)) 예) 9,999,999,999
    trfdtl_tast_vs: Optional[float] = None # 양도내역(총자산대비(%)(A/B))
    trfdtl_ecpt: Optional[int] = None # 양도내역(자기자본(원)(C)) 예) 9,999,999,999
    trfdtl_ecpt_vs: Optional[float] = None # 양도내역(자기자본대비(%)(A/C))
    attrf_owstkcnt: Optional[int] = None # 양도후 소유주식수 및 지분비율(소유주식수(주)) 예) 9,999,999,999
    attrf_eqrt: Optional[float] = None # 양도후 소유주식수 및 지분비율(지분비율(%))
    trf_pp: Optional[str] = None # 양도목적
    trf_prd: Optional[str] = None # 양도예정일자

    dlptn_cmpnm: Optional[str] = None # 거래상대방(회사명(성명))
    dlptn_cpt: Optional[int] = None # 거래상대방(자본금(원)) 예) 9,999,999,999
    dlptn_mbsn: Optional[str] = None # 거래상대방(주요사업)
    dlptn_hoadd: Optional[str] = None # 거래상대방(본점소재지(주소))
    dlptn_rl_cmpn: Optional[str] = None # 거래상대방(회사와의 관계)
    dl_pym: Optional[str] = None # 거래대금지급
    exevl_atn: Optional[str] = None # 외부평가에 관한 사항(외부평가 여부)
    exevl_bs_rs: Optional[str] = None # 외부평가에 관한 사항(근거 및 사유)
    exevl_intn: Optional[str] = None # 외부평가에 관한 사항(외부평가기관의 명칭)
    exevl_pd: Optional[str] = None # 외부평가에 관한 사항(외부평가 기간)
    exevl_op: Optional[str] = None # 외부평가에 관한 사항(외부평가 의견)
    bddd: Optional[str] = None # 이사회결의일(결정일)
    od_a_at_t: Optional[int] = None # 사외이사참석여부(참석(명)) 예) 9,999,999,999
    od_a_at_b: Optional[int] = None # 사외이사참석여부(불참(명)) 예) 9,999,999,999
    adt_a_atn: Optional[str] = None # 감사(사외이사가 아닌 감사위원) 참석여부
    bdlst_atn: Optional[str] = None # 우회상장 해당 여부
    n6m_tpai_plann: Optional[str] = None # 향후 6월이내 제3자배정 증자 등 계획
    iscmp_bdlst_sf_atn: Optional[str] = None # 발행회사(타법인)의 우회상장 요건 충족여부
    ftc_stt_atn: Optional[str] = None # 공정거래위원회 신고대상 여부
    popt_ctr_atn: Optional[str] = None # 풋옵션 등 계약 체결여부
    popt_ctr_cn: Optional[str] = None # 계약내용

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "OtherShareTransferDecisionData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class EquityLinkedBondsTransferDecisionData(BaseMaterialFactsData):
    """주권 관련 사채권 양수/양도 결정"""
    # 공통
    stkrtbd_kndn: Optional[str] = None # 주권 관련 사채권의 종류
    tm: Optional[str] = None # 주권 관련 사채권의 종류(회차)
    knd: Optional[str] = None # 주권 관련 사채권의 종류(종류)
    bdiscmp_cmpnm: Optional[str] = None # 사채권 발행회사(회사명)
    bdiscmp_nt: Optional[str] = None # 사채권 발행회사(국적)
    bdiscmp_rp: Optional[str] = None # 사채권 발행회사(대표자)
    bdiscmp_cpt: Optional[int] = None # 사채권 발행회사(자본금(원)) 예) 9,999,999,999
    bdiscmp_rl_cmpn: Optional[str] = None # 사채권 발행회사(회사와 관계)
    bdiscmp_tisstk: Optional[int] = None # 사채권 발행회사(발행주식 총수(주)) 예) 9,999,999,999
    bdiscmp_mbsn: Optional[str] = None # 사채권 발행회사(주요사업)
    # 양수
    l6m_tpa_nstkaq_atn: Optional[str] = None # 최근 6월 이내 제3자 배정에 의한 신주취득 여부
    inhdtl_bd_fta: Optional[int] = None # 양수내역(사채의 권면(전자등록)총액(원)) 예) 9,999,999,999
    inhdtl_inhprc: Optional[int] = None # 양수내역(양수금액(원)(A)) 예) 9,999,999,999
    inhdtl_tast: Optional[int] = None # 양수내역(총자산(원)(B)) 예) 9,999,999,999
    inhdtl_tast_vs: Optional[float] = None # 양수내역(총자산대비(%)(A/B))
    inhdtl_ecpt: Optional[int] = None # 양수내역(자기자본(원)(C)) 예) 9,999,999,999
    inhdtl_ecpt_vs: Optional[float] = None # 양수내역(자기자본대비(%)(A/C))
    inh_pp: Optional[str] = None # 양수목적
    inh_prd: Optional[str] = None # 양수예정일자
    # 양도
    aqd: Optional[str] = None # 취득일자
    trfdtl_bd_fta: Optional[int] = None # 양도내역(사채의 권면(전자등록)총액(원)) 예) 9,999,999,999
    trfdtl_trfprc: Optional[int] = None # 양도내역(양도금액(원)(A)) 예) 9,999,999,999
    trfdtl_tast: Optional[int] = None # 양도내역(총자산(원)(B)) 예) 9,999,999,999
    trfdtl_tast_vs: Optional[float] = None # 양도내역(총자산대비(%)(A/B))
    trfdtl_ecpt: Optional[int] = None # 양도내역(자기자본(원)(C)) 예) 9,999,999,999
    trfdtl_ecpt_vs: Optional[float] = None # 양도내역(자기자본대비(%)(A/C))
    trf_pp: Optional[str] = None # 양도목적
    trf_prd: Optional[str] = None # 양도예정일자
    # 공통
    dlptn_cmpnm: Optional[str] = None # 거래상대방(회사명(성명))
    dlptn_cpt: Optional[int] = None # 거래상대방(자본금(원)) 예) 9,999,999,999
    dlptn_mbsn: Optional[str] = None # 거래상대방(주요사업)
    dlptn_hoadd: Optional[str] = None # 거래상대방(본점소재지(주소))
    dlptn_rl_cmpn: Optional[str] = None # 거래상대방(회사와의 관계)
    dl_pym: Optional[str] = None # 거래대금지급
    exevl_atn: Optional[str] = None # 외부평가에 관한 사항(외부평가 여부)
    exevl_bs_rs: Optional[str] = None # 외부평가에 관한 사항(근거 및 사유)
    exevl_intn: Optional[str] = None # 외부평가에 관한 사항(외부평가기관의 명칭)
    exevl_pd: Optional[str] = None # 외부평가에 관한 사항(외부평가 기간)
    exevl_op: Optional[str] = None # 외부평가에 관한 사항(외부평가 의견)
    bddd: Optional[str] = None # 이사회결의일(결정일)
    od_a_at_t: Optional[int] = None # 사외이사 참석여부(참석(명)) 예) 9,999,999,999
    od_a_at_b: Optional[int] = None # 사외이사 참석여부(불참(명)) 예) 9,999,999,999
    adt_a_atn: Optional[str] = None # 감사(사외이사가 아닌 감사위원) 참석여부
    ftc_stt_atn: Optional[str] = None # 공정거래위원회 신고대상 여부
    popt_ctr_atn: Optional[str] = None # 풋옵션 등 계약 체결여부
    popt_ctr_cn: Optional[str] = None # 계약내용

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "EquityLinkedBondsTransferDecisionData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class CompanyMergerDecisionData(BaseMaterialFactsData):
    """회사합병 결정"""
    mg_mth: Optional[str] = None # 합병방법
    mg_stn: Optional[str] = None # 합병형태
    mg_pp: Optional[str] = None # 합병목적
    mg_rt: Optional[str] = None # 합병비율
    mg_rt_bs: Optional[str] = None # 합병비율 산출근거
    exevl_atn: Optional[str] = None # 외부평가에 관한 사항(외부평가 여부)
    exevl_bs_rs: Optional[str] = None # 외부평가에 관한 사항(근거 및 사유)
    exevl_intn: Optional[str] = None # 외부평가에 관한 사항(외부평가기관의 명칭)
    exevl_pd: Optional[str] = None # 외부평가에 관한 사항(외부평가 기간)
    exevl_op: Optional[str] = None # 외부평가에 관한 사항(외부평가 의견)
    mgnstk_ostk_cnt: Optional[int] = None # 합병신주의 종류와 수(주)(보통주식) 예) 9,999,999,999
    mgnstk_cstk_cnt: Optional[int] = None # 합병신주의 종류와 수(주)(종류주식) 예) 9,999,999,999
    mgptncmp_cmpnm: Optional[str] = None # 합병상대회사(회사명)
    mgptncmp_mbsn: Optional[str] = None # 합병상대회사(주요사업)
    mgptncmp_rl_cmpn: Optional[str] = None # 합병상대회사(회사와의 관계)
    rbsnfdtl_tast: Optional[int] = None # 합병상대회사(최근 사업연도 재무내용(원)(자산총계)) 예) 9,999,999,999
    rbsnfdtl_tdbt: Optional[int] = None # 합병상대회사(최근 사업연도 재무내용(원)(부채총계)) 예) 9,999,999,999
    rbsnfdtl_teqt: Optional[int] = None # 합병상대회사(최근 사업연도 재무내용(원)(자본총계)) 예) 9,999,999,999
    rbsnfdtl_cpt: Optional[int] = None # 합병상대회사(최근 사업연도 재무내용(원)(자본금)) 예) 9,999,999,999
    rbsnfdtl_sl: Optional[int] = None # 합병상대회사(최근 사업연도 재무내용(원)(매출액)) 예) 9,999,999,999
    rbsnfdtl_nic: Optional[int] = None # 합병상대회사(최근 사업연도 재무내용(원)(당기순이익)) 예) 9,999,999,999
    eadtat_intn: Optional[str] = None # 합병상대회사(외부감사 여부(기관명))
    eadtat_op: Optional[str] = None # 합병상대회사(외부감사 여부(감사의견))
    nmgcmp_cmpnm: Optional[str] = None # 신설합병회사(회사명)
    ffdtl_tast: Optional[int] = None # 신설합병회사(설립시 재무내용(원)(자산총계)) 예) 9,999,999,999
    ffdtl_tdbt: Optional[int] = None # 신설합병회사(설립시 재무내용(원)(부채총계)) 예) 9,999,999,999
    ffdtl_teqt: Optional[int] = None # 신설합병회사(설립시 재무내용(원)(자본총계)) 예) 9,999,999,999
    ffdtl_cpt: Optional[int] = None # 신설합병회사(설립시 재무내용(원)(자본금)) 예) 9,999,999,999
    ffdtl_std: Optional[int] = None # 신설합병회사(설립시 재무내용(원)(현재기준))
    nmgcmp_nbsn_rsl: Optional[int] = None # 신설합병회사(신설사업부문 최근 사업연도 매출액(원)) 예) 9,999,999,999
    nmgcmp_mbsn: Optional[str] = None # 신설합병회사(주요사업)
    nmgcmp_rlst_atn: Optional[str] = None # 신설합병회사(재상장신청 여부)
    mgsc_mgctrd: Optional[str] = None # 합병일정(합병계약일)
    mgsc_shddstd: Optional[str] = None # 합병일정(주주확정기준일)
    mgsc_shclspd_bgd: Optional[str] = None # 합병일정(주주명부 폐쇄기간(시작일))
    mgsc_shclspd_edd: Optional[str] = None # 합병일정(주주명부 폐쇄기간(종료일))
    mgsc_mgop_rcpd_bgd: Optional[str] = None # 합병일정(합병반대의사통지 접수기간(시작일))
    mgsc_mgop_rcpd_edd: Optional[str] = None # 합병일정(합병반대의사통지 접수기간(종료일))
    mgsc_gmtsck_prd: Optional[str] = None # 합병일정(주주총회예정일자)
    mgsc_aprskh_expd_bgd: Optional[str] = None # 합병일정(주식매수청구권 행사기간(시작일))
    mgsc_aprskh_expd_edd: Optional[str] = None # 합병일정(주식매수청구권 행사기간(종료일))
    mgsc_osprpd_bgd: Optional[str] = None # 합병일정(구주권 제출기간(시작일))
    mgsc_osprpd_edd: Optional[str] = None # 합병일정(구주권 제출기간(종료일))
    mgsc_trspprpd_bgd: Optional[str] = None # 합병일정(매매거래 정지예정기간(시작일))
    mgsc_trspprpd_edd: Optional[str] = None # 합병일정(매매거래 정지예정기간(종료일))
    mgsc_cdobprpd_bgd: Optional[str] = None # 합병일정(채권자이의 제출기간(시작일))
    mgsc_cdobprpd_edd: Optional[str] = None # 합병일정(채권자이의 제출기간(종료일))
    mgsc_mgdt: Optional[str] = None # 합병일정(합병기일)
    mgsc_ergmd: Optional[str] = None # 합병일정(종료보고 총회일)
    mgsc_mgrgsprd: Optional[str] = None # 합병일정(합병등기예정일자)
    mgsc_nstkdlprd: Optional[str] = None # 합병일정(신주권교부예정일)
    mgsc_nstklstprd: Optional[str] = None # 합병일정(신주의 상장예정일)
    bdlst_atn: Optional[str] = None # 우회상장 해당 여부
    otcpr_bdlst_sf_atn: Optional[str] = None # 타법인의 우회상장 요건 충족여부
    aprskh_plnprc: Optional[int] = None # 주식매수청구권에 관한 사항(매수예정가격) 예) 9,999,999,999
    aprskh_pym_plpd_mth: Optional[str] = None # 주식매수청구권에 관한 사항(지급예정시기, 지급방법)
    aprskh_ctref: Optional[str] = None # 주식매수청구권에 관한 사항(계약에 미치는 효력)
    bddd: Optional[str] = None # 이사회결의일(결정일)
    od_a_at_t: Optional[str] = None # 사외이사참석여부(참석(명))
    od_a_at_b: Optional[str] = None # 사외이사참석여부(불참(명))
    adt_a_atn: Optional[str] = None # 감사(사외이사가 아닌 감사위원) 참석여부
    popt_ctr_atn: Optional[str] = None # 풋옵션 등 계약 체결여부
    popt_ctr_cn: Optional[str] = None # 계약내용
    rs_sm_atn: Optional[str] = None # 증권신고서 제출대상 여부
    ex_sm_r: Optional[str] = None # 제출을 면제받은 경우 그 사유

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "CompanyMergerDecisionData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class CompanySpinoffDecisionData(BaseMaterialFactsData):
    """회사분할 결정"""
    dv_mth: Optional[str] = None # 분할방법
    dv_impef: Optional[str] = None # 분할의 중요영향 및 효과
    dv_rt: Optional[str] = None # 분할비율
    dv_trfbsnprt_cn: Optional[str] = None # 분할로 이전할 사업 및 재산의 내용
    atdv_excmp_cmpnm: Optional[str] = None # 분할 후 존속회사(회사명)
    atdvfdtl_tast: Optional[int] = None # 분할 후 존속회사(분할후 재무내용(원)(자산총계)) 예) 9,999,999,999
    atdvfdtl_tdbt: Optional[int] = None # 분할 후 존속회사(분할후 재무내용(원)(부채총계)) 예) 9,999,999,999
    atdvfdtl_teqt: Optional[int] = None # 분할 후 존속회사(분할후 재무내용(원)(자본총계)) 예) 9,999,999,999
    atdvfdtl_cpt: Optional[int] = None # 분할 후 존속회사(분할후 재무내용(원)(자본금)) 예) 9,999,999,999
    atdvfdtl_std: Optional[str] = None # 분할 후 존속회사(분할후 재무내용(원)(현재기준))
    atdv_excmp_exbsn_rsl: Optional[int] = None # 분할 후 존속회사(존속사업부문 최근 사업연도매출액(원)) 예) 9,999,999,999
    atdv_excmp_mbsn: Optional[str] = None # 분할 후 존속회사(주요사업)
    atdv_excmp_atdv_lstmn_atn: Optional[str] = None # 분할 후 존속회사(분할 후 상장유지 여부)
    dvfcmp_cmpnm: Optional[str] = None # 분할설립회사(회사명)
    ffdtl_tast: Optional[int] = None # 분할설립회사(설립시 재무내용(원)(자산총계)) 예) 9,999,999,999
    ffdtl_tdbt: Optional[int] = None # 분할설립회사(설립시 재무내용(원)(부채총계)) 예) 9,999,999,999
    ffdtl_teqt: Optional[int] = None # 분할설립회사(설립시 재무내용(원)(자본총계)) 예) 9,999,999,999
    ffdtl_cpt: Optional[int] = None # 분할설립회사(설립시 재무내용(원)(자본금)) 예) 9,999,999,999
    ffdtl_std: Optional[str] = None # 분할설립회사(설립시 재무내용(원)(현재기준))
    dvfcmp_nbsn_rsl: Optional[int] = None # 분할설립회사(신설사업부문 최근 사업연도 매출액(원)) 예) 9,999,999,999
    dvfcmp_mbsn: Optional[str] = None # 분할설립회사(주요사업)
    dvfcmp_rlst_atn: Optional[str] = None # 분할설립회사(재상장신청 여부)
    abcr_crrt: Optional[str] = None # 감자에 관한 사항(감자비율(%))
    abcr_osprpd_bgd: Optional[str] = None # 감자에 관한 사항(구주권 제출기간(시작일))
    abcr_osprpd_edd: Optional[str] = None # 감자에 관한 사항(구주권 제출기간(종료일))
    abcr_trspprpd_bgd: Optional[str] = None # 감자에 관한 사항(매매거래정지 예정기간(시작일))
    abcr_trspprpd_edd: Optional[str] = None # 감자에 관한 사항(매매거래정지 예정기간(종료일))
    abcr_nstkascnd: Optional[str] = None # 감자에 관한 사항(신주배정조건)
    abcr_shstkcnt_rt_at_rs: Optional[str] = None # 감자에 관한 사항(주주 주식수 비례여부 및 사유)
    abcr_nstkasstd: Optional[str] = None # 감자에 관한 사항(신주배정기준일)
    abcr_nstkdlprd: Optional[str] = None # 감자에 관한 사항(신주권교부예정일)
    abcr_nstklstprd: Optional[str] = None # 감자에 관한 사항(신주의 상장예정일)
    gmtsck_prd: Optional[str] = None # 주주총회 예정일
    cdobprpd_bgd: Optional[str] = None # 채권자 이의제출기간(시작일)
    cdobprpd_edd: Optional[str] = None # 채권자 이의제출기간(종료일)
    dvdt: Optional[str] = None # 분할기일
    dvrgsprd: Optional[str] = None # 분할등기 예정일
    bddd: Optional[str] = None # 이사회결의일(결정일)
    od_a_at_t: Optional[int] = None # 사외이사참석여부(참석(명)) 예) 9,999,999,999
    od_a_at_b: Optional[int] = None # 사외이사참석여부(불참(명)) 예) 9,999,999,999
    adt_a_atn: Optional[str] = None # 감사(사외이사가 아닌 감사위원) 참석여부
    popt_ctr_atn: Optional[str] = None # 풋옵션 등 계약 체결여부
    popt_ctr_cn: Optional[str] = None # 계약내용
    rs_sm_atn: Optional[str] = None # 증권신고서 제출대상 여부
    ex_sm_r: Optional[str] = None # 제출을 면제받은 경우 그 사유

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "CompanySpinoffDecisionData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class CompanySpinoffMergerDecisionData(BaseMaterialFactsData):
    """회사분할합병 결정"""
    dvmg_mth: Optional[str] = None # 분할합병 방법
    dvmg_impef: Optional[str] = None # 분할합병의 중요영향 및 효과
    dv_trfbsnprt_cn: Optional[str] = None # 분할에 관한 사항(분할로 이전할 사업 및 재산의 내용)
    atdv_excmp_cmpnm: Optional[str] = None # 분할에 관한 사항(분할 후 존속회사(회사명))
    atdvfdtl_tast: Optional[int] = None # 분할에 관한 사항(분할 후 존속회사(분할후 재무내용(원)(자산총계))) 예) 9,999,999,999
    atdvfdtl_tdbt: Optional[int] = None # 분할에 관한 사항(분할 후 존속회사(분할후 재무내용(원)(부채총계))) 예) 9,999,999,999
    atdvfdtl_teqt: Optional[int] = None # 분할에 관한 사항(분할 후 존속회사(분할후 재무내용(원)(자본총계))) 예) 9,999,999,999
    atdvfdtl_cpt: Optional[int] = None # 분할에 관한 사항(분할 후 존속회사(분할후 재무내용(원)(자본금))) 예) 9,999,999,999
    atdvfdtl_std: Optional[str] = None # 분할에 관한 사항(분할 후 존속회사(분할후 재무내용(원)(현재기준)))
    atdv_excmp_exbsn_rsl: Optional[int] = None # 분할에 관한 사항(분할 후 존속회사(존속사업부문 최근 사업연도매출액(원))) 예) 9,999,999,999
    atdv_excmp_mbsn: Optional[str] = None # 분할에 관한 사항(분할 후 존속회사(주요사업))
    atdv_excmp_atdv_lstmn_atn: Optional[str] = None # 분할에 관한 사항(분할 후 존속회사(분할 후 상장유지 여부))
    dvfcmp_cmpnm: Optional[str] = None # 분할에 관한 사항(분할설립 회사(회사명))
    ffdtl_tast: Optional[int] = None # 분할에 관한 사항(분할설립 회사(설립시 재무내용(원)(자산총계))) 예) 9,999,999,999
    ffdtl_tdbt: Optional[int] = None # 분할에 관한 사항(분할설립 회사(설립시 재무내용(원)(부채총계))) 예) 9,999,999,999
    ffdtl_teqt: Optional[int] = None # 분할에 관한 사항(분할설립 회사(설립시 재무내용(원)(자본총계))) 예) 9,999,999,999
    ffdtl_cpt: Optional[int] = None # 분할에 관한 사항(분할설립 회사(설립시 재무내용(원)(자본금))) 예) 9,999,999,999
    ffdtl_std: Optional[str] = None # 분할에 관한 사항(분할설립 회사(설립시 재무내용(원)(현재기준)))
    dvfcmp_nbsn_rsl: Optional[int] = None # 분할에 관한 사항(분할설립 회사(신설사업부문 최근 사업연도 매출액(원))) 예) 9,999,999,999
    dvfcmp_mbsn: Optional[str] = None # 분할에 관한 사항(분할설립 회사(주요사업))
    dvfcmp_atdv_lstmn_at: Optional[str] = None # 분할에 관한 사항(분할설립 회사(분할후 상장유지여부))
    abcr_crrt: Optional[float] = None # 분할에 관한 사항(감자에 관한 사항(감자비율(%)))
    abcr_osprpd_bgd: Optional[str] = None # 분할에 관한 사항(감자에 관한 사항(구주권 제출기간(시작일)))
    abcr_osprpd_edd: Optional[str] = None # 분할에 관한 사항(감자에 관한 사항(구주권 제출기간(종료일)))
    abcr_trspprpd_bgd: Optional[str] = None # 분할에 관한 사항(감자에 관한 사항(매매거래정지 예정기간(시작일)))
    abcr_trspprpd_edd: Optional[str] = None # 분할에 관한 사항(감자에 관한 사항(매매거래정지 예정기간(종료일)))
    abcr_nstkascnd: Optional[str] = None # 분할에 관한 사항(감자에 관한 사항(신주배정조건))
    abcr_shstkcnt_rt_at_rs: Optional[str] = None # 분할에 관한 사항(감자에 관한 사항(주주 주식수 비례여부 및 사유))
    abcr_nstkasstd: Optional[str] = None # 분할에 관한 사항(감자에 관한 사항(신주배정기준일))
    abcr_nstkdlprd: Optional[str] = None # 분할에 관한 사항(감자에 관한 사항(신주권교부예정일))
    abcr_nstklstprd: Optional[str] = None # 분할에 관한 사항(감자에 관한 사항(신주의 상장예정일))
    mg_stn: Optional[str] = None # 합병에 관한 사항(합병형태)
    mgptncmp_cmpnm: Optional[str] = None # 합병에 관한 사항(합병상대 회사(회사명))
    mgptncmp_mbsn: Optional[str] = None # 합병에 관한 사항(합병상대 회사(주요사업))
    mgptncmp_rl_cmpn: Optional[str] = None # 합병에 관한 사항(합병상대 회사(회사와의 관계))
    rbsnfdtl_tast: Optional[int] = None # 합병에 관한 사항(합병상대 회사(최근 사업연도 재무내용(원)(자산총계))) 예) 9,999,999,999
    rbsnfdtl_tdbt: Optional[int] = None # 합병에 관한 사항(합병상대 회사(최근 사업연도 재무내용(원)(부채총계))) 예) 9,999,999,999
    rbsnfdtl_teqt: Optional[int] = None # 합병에 관한 사항(합병상대 회사(최근 사업연도 재무내용(원)(자본총계))) 예) 9,999,999,999
    rbsnfdtl_cpt: Optional[int] = None # 합병에 관한 사항(합병상대 회사(최근 사업연도 재무내용(원)(자본금))) 예) 9,999,999,999
    rbsnfdtl_sl: Optional[int] = None # 합병에 관한 사항(합병상대 회사(최근 사업연도 재무내용(원)(매출액))) 예) 9,999,999,999
    rbsnfdtl_nic: Optional[int] = None # 합병에 관한 사항(합병상대 회사(최근 사업연도 재무내용(원)(당기순이익))) 예) 9,999,999,999
    eadtat_intn: Optional[str] = None # 합병에 관한 사항(합병상대 회사(외부감사 여부(기관명)))
    eadtat_op: Optional[str] = None # 합병에 관한 사항(합병상대 회사(외부감사 여부(감사의견)))
    dvmgnstk_ostk_cnt: Optional[int] = None # 합병에 관한 사항(분할합병신주의 종류와 수(주)(보통주식)) 예) 9,999,999,999
    dvmgnstk_cstk_cnt: Optional[int] = None # 합병에 관한 사항(분할합병신주의 종류와 수(주)(종류주식)) 예) 9,999,999,999
    nmgcmp_cmpnm: Optional[str] = None # 합병에 관한 사항(합병신설 회사(회사명))
    nmgcmp_cpt: Optional[int] = None # 합병에 관한 사항(합병신설 회사(자본금(원))) 예) 9,999,999,999
    nmgcmp_mbsn: Optional[str] = None # 합병에 관한 사항(합병신설 회사(주요사업))
    nmgcmp_rlst_atn: Optional[str] = None # 합병에 관한 사항(합병신설 회사(재상장신청 여부))
    dvmg_rt: Optional[str] = None # 분할합병비율
    dvmg_rt_bs: Optional[str] = None # 분할합병비율 산출근거
    exevl_atn: Optional[str] = None # 외부평가에 관한 사항(외부평가 여부)
    exevl_bs_rs: Optional[str] = None # 외부평가에 관한 사항(근거 및 사유)
    exevl_intn: Optional[str] = None # 외부평가에 관한 사항(외부평가기관의 명칭)
    exevl_pd: Optional[str] = None # 외부평가에 관한 사항(외부평가 기간)
    exevl_op: Optional[str] = None # 외부평가에 관한 사항(외부평가 의견)
    dvmgsc_dvmgctrd: Optional[str] = None # 분할합병일정(분할합병계약일)
    dvmgsc_shddstd: Optional[str] = None # 분할합병일정(주주확정기준일)
    dvmgsc_shclspd_bgd: Optional[str] = None # 분할합병일정(주주명부 폐쇄기간(시작일))
    dvmgsc_shclspd_edd: Optional[str] = None # 분할합병일정(주주명부 폐쇄기간(종료일))
    dvmgsc_dvmgop_rcpd_bgd: Optional[str] = None # 분할합병일정(분할합병반대의사통지 접수기간(시작일))
    dvmgsc_dvmgop_rcpd_edd: Optional[str] = None # 분할합병일정(분할합병반대의사통지 접수기간(종료일))
    dvmgsc_gmtsck_prd: Optional[str] = None # 분할합병일정(주주총회예정일자)
    dvmgsc_aprskh_expd_bgd: Optional[str] = None # 분할합병일정(주식매수청구권 행사기간(시작일))
    dvmgsc_aprskh_expd_edd: Optional[str] = None # 분할합병일정(주식매수청구권 행사기간(종료일))
    dvmgsc_cdobprpd_bgd: Optional[str] = None # 분할합병일정(채권자 이의 제출기간(시작일))
    dvmgsc_cdobprpd_edd: Optional[str] = None # 분할합병일정(채권자 이의 제출기간(종료일))
    dvmgsc_dvmgdt: Optional[str] = None # 분할합병일정(분할합병기일)
    dvmgsc_ergmd: Optional[str] = None # 분할합병일정(종료보고 총회일)
    dvmgsc_dvmgrgsprd: Optional[str] = None # 분할합병일정(분할합병등기예정일)
    bdlst_atn: Optional[str] = None # 우회상장 해당 여부
    otcpr_bdlst_sf_atn: Optional[str] = None # 타법인의 우회상장 요건 충족여부
    aprskh_exrq: Optional[str] = None # 주식매수청구권에 관한 사항(행사요건)
    aprskh_plnprc: Optional[str] = None # 주식매수청구권에 관한 사항(매수예정가격)
    aprskh_ex_pc_mth_pd_pl: Optional[str] = None # 주식매수청구권에 관한 사항(행사절차, 방법, 기간, 장소)
    aprskh_pym_plpd_mth: Optional[str] = None # 주식매수청구권에 관한 사항(지급예정시기, 지급방법)
    aprskh_lmt: Optional[str] = None # 주식매수청구권에 관한 사항(주식매수청구권 제한 관련 내용)
    aprskh_ctref: Optional[str] = None # 주식매수청구권에 관한 사항(계약에 미치는 효력)
    bddd: Optional[str] = None # 이사회결의일(결정일)
    od_a_at_t: Optional[int] = None # 사외이사참석여부(참석(명)) 예) 9,999,999,999
    od_a_at_b: Optional[int] = None # 사외이사참석여부(불참(명)) 예) 9,999,999,999
    adt_a_atn: Optional[str] = None # 감사(사외이사가 아닌 감사위원) 참석여부
    popt_ctr_atn: Optional[str] = None # 풋옵션 등 계약 체결여부
    popt_ctr_cn: Optional[str] = None # 계약내용
    rs_sm_atn: Optional[str] = None # 증권신고서 제출대상 여부
    ex_sm_r: Optional[str] = None # 제출을 면제받은 경우 그 사유

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "CompanySpinoffMergerDecisionData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)

@dataclass
class ShareExchangeDecisionData(BaseMaterialFactsData):
    """주식교환·이전 결정"""
    extr_sen: Optional[str] = None # 구분
    extr_stn: Optional[str] = None # 교환ㆍ이전 형태
    extr_tgcmp_cmpnm: Optional[str] = None # 교환ㆍ이전 대상법인(회사명)
    extr_tgcmp_rp: Optional[str] = None # 교환ㆍ이전 대상법인(대표자)
    extr_tgcmp_mbsn: Optional[str] = None # 교환ㆍ이전 대상법인(주요사업)
    extr_tgcmp_rl_cmpn: Optional[str] = None # 교환ㆍ이전 대상법인(회사와의 관계)
    extr_tgcmp_tisstk_ostk: Optional[int] = None # 교환ㆍ이전 대상법인(발행주식총수(주)(보통주식)) 예) 9,999,999,999
    extr_tgcmp_tisstk_cstk: Optional[int] = None # 교환ㆍ이전 대상법인(발행주식총수(주)(종류주식)) 예) 9,999,999,999
    rbsnfdtl_tast: Optional[int] = None # 교환ㆍ이전 대상법인(최근 사업연도 요약재무내용(원)(자산총계)) 예) 9,999,999,999
    rbsnfdtl_tdbt: Optional[int] = None # 교환ㆍ이전 대상법인(최근 사업연도 요약재무내용(원)(부채총계)) 예) 9,999,999,999
    rbsnfdtl_teqt: Optional[int] = None # 교환ㆍ이전 대상법인(최근 사업연도 요약재무내용(원)(자본총계)) 예) 9,999,999,999
    rbsnfdtl_cpt: Optional[int] = None # 교환ㆍ이전 대상법인(최근 사업연도 요약재무내용(원)(자본금)) 예) 9,999,999,999
    extr_rt: Optional[str] = None # 교환ㆍ이전 비율
    extr_rt_bs: Optional[str] = None # 교환ㆍ이전 비율 산출근거
    exevl_atn: Optional[str] = None # 외부평가에 관한 사항(외부평가 여부)
    exevl_bs_rs: Optional[str] = None # 외부평가에 관한 사항(근거 및 사유)
    exevl_intn: Optional[str] = None # 외부평가에 관한 사항(외부평가기관의 명칭)
    exevl_pd: Optional[str] = None # 외부평가에 관한 사항(외부평가 기간)
    exevl_op: Optional[str] = None # 외부평가에 관한 사항(외부평가 의견)
    extr_pp: Optional[str] = None # 교환ㆍ이전 목적
    extrsc_extrctrd: Optional[str] = None # 교환ㆍ이전일정(교환ㆍ이전계약일)
    extrsc_shddstd: Optional[str] = None # 교환ㆍ이전일정(주주확정기준일)
    extrsc_shclspd_bgd: Optional[str] = None # 교환ㆍ이전일정(주주명부 폐쇄기간(시작일))
    extrsc_shclspd_edd: Optional[str] = None # 교환ㆍ이전일정(주주명부 폐쇄기간(종료일))
    extrsc_extrop_rcpd_bgd: Optional[str] = None # 교환ㆍ이전일정(주식교환ㆍ이전 반대의사 통지접수기간(시작일))
    extrsc_extrop_rcpd_edd: Optional[str] = None # 교환ㆍ이전일정(주식교환ㆍ이전 반대의사 통지접수기간(종료일))
    extrsc_gmtsck_prd: Optional[str] = None # 교환ㆍ이전일정(주주총회 예정일자)
    extrsc_aprskh_expd_bgd: Optional[str] = None # 교환ㆍ이전일정(주식매수청구권 행사기간(시작일))
    extrsc_aprskh_expd_edd: Optional[str] = None # 교환ㆍ이전일정(주식매수청구권 행사기간(종료일))
    extrsc_osprpd_bgd: Optional[str] = None # 교환ㆍ이전일정(구주권제출기간(시작일))
    extrsc_osprpd_edd: Optional[str] = None # 교환ㆍ이전일정(구주권제출기간(종료일))
    extrsc_trspprpd: Optional[str] = None # 교환ㆍ이전일정(매매거래정지예정기간)
    extrsc_trspprpd_bgd: Optional[str] = None # 교환ㆍ이전일정(매매거래정지예정기간(시작일))
    extrsc_trspprpd_edd: Optional[str] = None # 교환ㆍ이전일정(매매거래정지예정기간(종료일))
    extrsc_extrdt: Optional[str] = None # 교환ㆍ이전일정(교환ㆍ이전일자)
    extrsc_nstkdlprd: Optional[str] = None # 교환ㆍ이전일정(신주권교부예정일)
    extrsc_nstklstprd: Optional[str] = None # 교환ㆍ이전일정(신주의 상장예정일)
    atextr_cpcmpnm: Optional[str] = None # 교환ㆍ이전 후 완전모회사명
    aprskh_plnprc: Optional[int] = None # 주식매수청구권에 관한 사항(매수예정가격) 예) 9,999,999,999
    aprskh_pym_plpd_mth: Optional[str] = None # 주식매수청구권에 관한 사항(지급예정시기, 지급방법)
    aprskh_lmt: Optional[str] = None # 주식매수청구권에 관한 사항(주식매수청구권 제한 관련 내용)
    aprskh_ctref: Optional[str] = None # 주식매수청구권에 관한 사항(계약에 미치는 효력)
    bdlst_atn: Optional[str] = None # 우회상장 해당 여부
    otcpr_bdlst_sf_atn: Optional[str] = None # 타법인의 우회상장 요건 충족 여부
    bddd: Optional[str] = None # 이사회결의일(결정일)
    od_a_at_t: Optional[int] = None # 사외이사참석여부(참석(명)) 예) 9,999,999,999
    od_a_at_b: Optional[int] = None # 사외이사참석여부(불참(명)) 예) 9,999,999,999
    adt_a_atn: Optional[str] = None # 참석여부	감사(사외이사가 아닌 감사위원) 참석여부
    popt_ctr_atn: Optional[str] = None # 풋옵션 등 계약 체결여부
    popt_ctr_cn: Optional[str] = None # 계약내용
    rs_sm_atn: Optional[str] = None # 증권신고서 제출대상 여부
    ex_sm_r: Optional[str] = None # 제출을 면제받은 경우 그 사유

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, str]) -> "ShareExchangeDecisionData":
        """딕셔너리에서 데이터 클래스 생성"""
        return cls(**raw_data)