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
from typing import Dict, Any, Optional, ClassVar

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


DISCLOSURE_COLUMNS = {
    "crtfc_key": "API 인증키",
    "bgn_de": "시작일",
    "end_de": "종료일",
    "last_reprt_at": "최종보고서 검색여부",
    "pblntf_ty": "공시유형",
    "pblntf_detail_ty": "공시상세유형",
    "sort": "정렬",
    "sort_mth": "정렬방법",
    "page_no": "페이지 번호",
    "page_count": "페이지 별 건수",

    "corp_cls": "법인구분",
    "corp_code": "고유번호",
    "corp_name": "종목명(법인명)",
    "corp_name_eng": "영문명칭",
    "corp_eng_name": "영문 정식명칭",
    "stock_name": "종목명(상장사) 또는 약식명칭(기타법인)",
    "stock_code": "상장회사인 경우 주식의 종목코드",
    "report_nm": "보고서명",
    "rcept_no": "접수번호",
    "flr_nm": "공시 제출인명",
    "rm": "비고",
    "ceo_nm": "대표자명",
    "jurir_no": "법인등록번호",
    "bizr_no": "사업자등록번호",
    "adres": "주소",
    "hm_url": "홈페이지",
    "ir_url": "IR홈페이지",
    "phn_no": "전화번호",
    "fax_no": "팩스번호",
    "induty_code": "업종코드",
    "est_dt": "설립일(YYYYMMDD)",
    "acc_mt": "결산월(MM)",
    "rcept_dt": "접수일자",
    "modify_date": "최종변경일자",
}

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

    Attributes:
        corp_cls: 법인구분
        corp_code: 고유번호
        corp_name: 종목명(법인명)
        corp_name_eng: 영문명칭
        corp_eng_name: 영문 정식명칭
        stock_name: 종목명(상장사) 또는 약식명칭(기타법인)
        stock_code: 상장회사인 경우 주식의 종목코드
        report_nm: 보고서명
        rcept_no: 접수번호
        flr_nm: 공시 제출인명
        rm: 비고
        ceo_nm: 대표자명
        jurir_no: 법인등록번호
        bizr_no: 사업자등록번호
        adres: 주소
        hm_url: 홈페이지
        ir_url: IR홈페이지
        phn_no: 전화번호
        fax_no: 팩스번호
        induty_code: 업종코드
        est_dt: 설립일(YYYYMMDD)
        acc_mt: 결산월(MM)
        rcept_dt: 접수일자
        modify_date: 최종변경일자
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

REPORTS_COLUMNS = {
    "crtfc_key": "API 인증키",
    "corp_code": "고유번호",
    "bsns_year": "사업연도",
    "reprt_code": "보고서 코드",
    "rcept_no": "접수번호",
    "corp_cls": "법인구분",
    "corp_name": "법인명",
    "isu_dcrs_de": "주식발행 감소일자",
    "isu_dcrs_stle": "발행 감소 형태",
    "isu_dcrs_stock_knd": "발행 감소 주식 종류",
    "isu_dcrs_qy": "발행 감소 수량",
    "isu_dcrs_mstvdv_fval_amount": "발행 감소 주당 액면 가액",
    "isu_dcrs_mstvdv_amount": "발행 감소 주당 가액",
    "se": "구분",
    "se_nm": "구분",
    "stock_knd": "주식 종류",
    "thstrm": "당기",
    "frmtrm": "전기",
    "lwfr": "전전기",
    "acqs_mth1": "취득방법 대분류",
    "acqs_mth2": "취득방법 중분류",
    "acqs_mth3": "취득방법 소분류",
    "bsis_qy": "기초 수량",
    "change_qy_acqs": "변동 수량 취득",
    "change_qy_dsps": "변동 수량 처분",
    "change_qy_incnr": "변동 수량 소각",
    "trmend_qy": "기말 수량",
    "nm": "성명",
    "relate": "관계",
    "bsis_posesn_stock_co": "기초 소유 주식 수",
    "bsis_posesn_stock_qota_rt": "기초 소유 주식 지분율",
    "trmend_posesn_stock_co": "기말 소유 주식 수",
    "trmend_posesn_stock_qota_rt": "기말 소유 주식 지분율",
    "change_on": "변동일",
    "mxmm_shrholdr_nm": "최대 주주명",
    "posesn_stock_co": "소유 주식수",
    "qota_rt": "지분율",
    "change_cause": "변동원인",
    "shrholdr_co": "주주수",
    "shrholdr_tot_co": "전체 주주수",
    "shrholdr_rate": "주주 비율",
    "hold_stock_co": "보유 주식수",
    "stock_tot_co": "총발행 주식수",
    "hold_stock_rate": "보유 주식 비율",
    "sexdstn": "성별",
    "birth_ym": "출생 년월",
    "ofcps": "직위",
    "rgist_exctv_at": "등기 임원 여부",
    "fte_at": "상근 여부",
    "chrg_job": "담당 업무",
    "main_career": "주요 경력",
    "mxmm_shrholdr_relate": "최대 주주 관계",
    "hffc_pd": "재직 기간",
    "tenure_end_on": "임기 만료일",
    "fo_bbm": "사업부문",
    "reform_bfe_emp_co_rgllbr": "개정 전 직원 수 정규직",
    "reform_bfe_emp_co_cnttk": "개정 전 직원 수 계약직",
    "reform_bfe_emp_co_etc": "개정 전 직원 수 기타",
    "rgllbr_co": "정규직 수",
    "rgllbr_abacpt_labrr_co": "정규직 단시간 근로자 수",
    "cnttk_co": "계약직 수",
    "cnttk_abacpt_labrr_co": "계약직 단시간 근로자 수",
    "sm": "합계",
    "avrg_cnwk_sdytrn": "평균 근속 연수",
    "fyer_salary_totamt": "연간 급여 총액",
    "jan_salary_am": "1인평균 급여 액",
    "mendng_totamt": "보수 총액",
    "mendng_totamt_ct_incls_mendng": "보수 총액 비 포함 보수",
    "nmpr": "인원수",
    "jan_avrg_mendng_am": "1인 평균 보수 액",
    "inv_prm": "법인명",
    "frst_acqs_de": "최초 취득 일자",
    "invstmnt_purps": "출자 목적",
    "frst_acqs_amount": "최초 취득 금액",
    "bsis_blce_qy": "기초 잔액 수량",
    "bsis_blce_qota_rt": "기초 잔액 지분율",
    "bsis_blce_acntbk_amount": "기초 잔액 장부 가액",
    "incrs_dcrs_acqs_dsps_qy": "증가 감소 취득 처분 수량",
    "incrs_dcrs_acqs_dsps_amount": "증가 감소 취득 처분 금액",
    "incrs_dcrs_evl_lstmn": "증가 감소 평가 손액",
    "trmend_blce_qy": "기말 잔액 수량",
    "trmend_blce_qota_rt": "기말 잔액 지분율",
    "trmend_blce_acntbk_amount": "기말 잔액 장부 가액",
    "recent_bsns_year_fnnr_sttus_tot_assets": "최근 사업 연도 재무 현황 총 자산",
    "recent_bsns_year_fnnr_sttus_thstrm_ntpf": "최근 사업 연도 재무 현황 당기 순이익",
    "isu_stock_totqy": "발행할 주식의 총수",
    "now_to_isu_stock_totqy": "현재까지 발행한 주식의 총수",
    "now_to_dcrs_stock_totqy": "현재까지 감소한 주식의 총수",
    "redc": "감자",
    "profit_incnr": "이익소각",
    "rdmstk_repy": "상환주식의 상환",
    "etc": "기타",
    "istc_totqy": "발행주식의 총수",
    "tesstk_co": "자기주식수",
    "distb_stock_co": "유통주식수",
    "scrits_knd_nm": "증권종류",
    "isu_mth_nm": "발행방법",
    "isu_de": "발행일자",
    "facvalu_totamt": "권면(전자등록)총액",
    "intrt": "이자율",
    "evl_grad_instt": "평가등급(평가기관)",
    "mtd": "만기일",
    "repy_at": "상환여부",
    "mngt_cmpny": "주관회사",
    "remndr_exprtn1": "잔여만기",
    "remndr_exprtn2": "잔여만기",
    "de10_below": "10일 이하",
    "de10_excess_de30_below": "10일초과 30일이하",
    "de30_excess_de90_below": "30일초과 90일이하",
    "de90_excess_de180_below": "90일초과 180일이하",
    "de180_excess_yy1_below": "180일초과 1년이하",
    "yy1_below": "1년 이하",
    "yy1_excess_yy2_below": "1년초과 2년이하",
    "yy2_excess_yy3_below": "2년초과 3년이하",
    "yy3_excess_yy4_below": "3년초과 4년이하",
    "yy4_excess_yy5_below": "4년초과 5년이하",
    "yy5_excess_yy10_below": "5년초과 10년이하",
    "yy10_excess_yy20_below": "10년초과 20년이하",
    "yy10_excess": "10년초과",
    "yy1_excess_yy5_below": "1년초과 5년이하",
    "yy10_excess_yy15_below": "10년초과 15년이하",
    "yy15_excess_yy20_below": "15년초과 20년이하",
    "yy20_excess_yy30_below": "20년초과 30년이하",
    "yy30_excess": "30년초과",
    "isu_lmt": "발행 한도",
    "remndr_lmt": "잔여 한도",
    "adtor": "감사인",
    "adt_opinion": "감사의견",
    "adt_reprt_spcmnt_matter": "감사보고서 특기사항",
    "emphs_matter": "강조사항 등",
    "core_adt_matter": "핵심감사사항",
    "cn": "내용",
    "mendng": "보수",
    "tot_reqre_time": "총소요시간",
    "adt_cntrct_dtls_mendng": "감사계약내역(보수)",
    "adt_cntrct_dtls_time": "감사계약내역(시간)",
    "real_exc_dtls_mendng": "실제수행내역(보수)",
    "real_exc_dtls_time": "실제수행내역(시간)",
    "cntrct_cncls_de": "계약체결일",
    "servc_cn": "용역내용",
    "servc_exc_pd": "용역수행기간",
    "servc_mendng": "용역보수",
    "drctr_co": "이사의 수",
    "otcmp_drctr_co": "사외이사 수",
    "apnt": "사외이사 변동현황(선임)",
    "rlsofc": "사외이사 변동현황(해임)",
    "mdstrm_resig": "사외이사 변동현황(중도퇴임)",
    "gmtsck_confm_amount": "주주총회 승인금액",
    "pymnt_totamt": "보수총액",
    "psn1_avrg_pymntamt": "1인당 평균보수액",
    "tm": "회차",
    "pay_de": "납입일",
    "pay_amount": "납입금액",
    "on_dclrt_cptal_use_plan": "신고서상 자금사용 계획",
    "real_cptal_use_sttus": "실제 자금사용 현황",
    "rs_cptal_use_plan_useprps": "증권신고서 등의 자금사용 계획(사용용도)",
    "rs_cptal_use_plan_prcure_amount": "증권신고서 등의 자금사용 계획(조달금액)",
    "real_cptal_use_dtls_cn": "실제 자금사용 내역(내용)",
    "real_cptal_use_dtls_amount": "실제 자금사용 내역(금액)",
    "dffrnc_occrrnc_resn": "차이발생 사유 등",
    "cptal_use_plan": "자금사용 계획",
    "mtrpt_cptal_use_plan_useprps": "주요사항보고서의 자금사용 계획(사용용도)",
    "mtrpt_cptal_use_plan_prcure_amount": "주요사항보고서의 자금사용 계획(조달금액)",
    "rm": "비고",
    "stlm_dt": "결산기준일",
}

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
    rcept_no: Optional[str] = None # 법접수번호
    corp_code: Optional[str] = None # 고유번호
    corp_cls: Optional[CorpClass] = None # 법인구분
    corp_name: Optional[str] = None # 법인명

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

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
