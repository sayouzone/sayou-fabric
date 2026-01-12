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

import json
import pandas as pd

from dataclasses import dataclass, field, asdict
from datetime import datetime
from decimal import Decimal
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple

from .base_model import ResponseBody

"""
Koreainvestment (KIS) Data Models
"""

@dataclass
class BalanceQueryParam:
    CANO: str               # 종합계좌번호
    ACNT_PRDT_CD: str       # 계좌상품코드
    AFHR_FLPR_YN: str       # 시간외단일가, 거래소여부
    INQR_DVSN: str          # 조회구분
    UNPR_DVSN: str          # 단가구분
    FUND_STTL_ICLD_YN: str  # 펀드결제분포함여부
    FNCG_AMT_AUTO_RDPT_YN: str    # 융자금액자동상환여부
    PRCS_DVSN: str          # 처리구분

    OFL_YN: Optional[str] = None            # 오프라인여부
    CTX_AREA_FK100: Optional[str] = None    # 연속조회검색조건100
    CTX_AREA_NK100: Optional[str] = None    # 연속조회키100

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class DomesticStockBalance:
    """국내주식 개별 종목 잔고 정보 (output1)."""
    
    # API 응답에 포함될 수 있는 필드들
    # 현재 데이터에는 빈 배열이지만, 일반적인 국내주식 잔고 필드 구조
    pdno: str = ""                        # 상품번호 (종목코드)
    prdt_name: str = ""                   # 상품명
    hldg_qty: int = 0                     # 보유수량
    ord_psbl_qty: int = 0                 # 주문가능수량
    pchs_avg_pric: Decimal = Decimal("0") # 매입평균가격
    pchs_amt: Decimal = Decimal("0")      # 매입금액
    prpr: Decimal = Decimal("0")          # 현재가
    evlu_amt: Decimal = Decimal("0")      # 평가금액
    evlu_pfls_amt: Decimal = Decimal("0") # 평가손익금액
    evlu_pfls_rt: Decimal = Decimal("0")  # 평가손익률

    FIELD_NAMES_KO = {
        "pdno": "종목코드",
        "prdt_name": "상품명",
        "hldg_qty": "보유수량",
        "ord_psbl_qty": "주문가능수량",
        "pchs_avg_pric": "매입평균가격",
        "pchs_amt": "매입금액",
        "prpr": "현재가",
        "evlu_amt": "평가금액",
        "evlu_pfls_amt": "평가손익금액",
        "evlu_pfls_rt": "평가손익률",
    }

    @classmethod
    def from_dict(cls, data: dict) -> "DomesticStockBalance":
        """딕셔너리에서 DomesticStockBalance 객체 생성."""
        return cls(
            pdno=data.get("pdno", ""),
            prdt_name=data.get("prdt_name", ""),
            hldg_qty=int(data.get("hldg_qty", 0)),
            ord_psbl_qty=int(data.get("ord_psbl_qty", 0)),
            pchs_avg_pric=Decimal(data.get("pchs_avg_pric", "0")),
            pchs_amt=Decimal(data.get("pchs_amt", "0")),
            prpr=Decimal(data.get("prpr", "0")),
            evlu_amt=Decimal(data.get("evlu_amt", "0")),
            evlu_pfls_amt=Decimal(data.get("evlu_pfls_amt", "0")),
            evlu_pfls_rt=Decimal(data.get("evlu_pfls_rt", "0")),
        )

    def to_korean(self) -> dict:
        """필드명을 한글로 변환한 딕셔너리 반환."""
        def format_value(v):
            if isinstance(v, Decimal):
                # 불필요한 소수점 이하 0 제거 후 천단위 구분자 적용
                normalized = v.normalize()
                if normalized == normalized.to_integral_value():
                    return f"{int(normalized):,}"
                return f"{normalized:,f}"
            return v
        
        return {
            self.FIELD_NAMES_KO.get(k, k): format_value(v)
            for k, v in self.__dict__.items()
            if v is not None
        }


@dataclass
class DomesticAccountSummary:
    """국내주식 계좌 요약 정보 (output2)."""
    
    dnca_tot_amt: Decimal       # 예수금총금액
    nxdy_excc_amt: Decimal      # 익일정산금액
    prvs_rcdl_excc_amt: Decimal # 가수도정산금액
    cma_evlu_amt: Decimal       # CMA평가금액
    bfdy_buy_amt: Decimal       # 전일매수금액
    thdt_buy_amt: Decimal       # 금일매수금액
    nxdy_auto_rdpt_amt: Decimal # 익일자동상환금액
    bfdy_sll_amt: Decimal       # 전일매도금액
    thdt_sll_amt: Decimal       # 금일매도금액
    d2_auto_rdpt_amt: Decimal   # D+2자동상환금액
    bfdy_tlex_amt: Decimal      # 전일제비용금액
    thdt_tlex_amt: Decimal      # 금일제비용금액
    tot_loan_amt: Decimal       # 총대출금액
    scts_evlu_amt: Decimal      # 유가증권평가금액
    tot_evlu_amt: Decimal       # 총평가금액
    nass_amt: Decimal           # 순자산금액
    fncg_gld_auto_rdpt_yn: str  # 융자금자동상환여부
    pchs_amt_smtl_amt: Decimal  # 매입금액합계금액
    evlu_amt_smtl_amt: Decimal  # 평가금액합계금액
    evlu_pfls_smtl_amt: Decimal # 평가손익합계금액
    tot_stln_slng_chgs: Decimal # 총대주매각대금
    bfdy_tot_asst_evlu_amt: Decimal # 전일총자산평가금액
    asst_icdc_amt: Decimal      # 자산증감금액
    asst_icdc_erng_rt: Decimal  # 자산증감수익률

    FIELD_NAMES_KO = {
        "dnca_tot_amt": "예수금총금액",
        "nxdy_excc_amt": "익일정산금액",
        "prvs_rcdl_excc_amt": "가수도정산금액",
        "cma_evlu_amt": "CMA평가금액",
        "bfdy_buy_amt": "전일매수금액",
        "thdt_buy_amt": "금일매수금액",
        "nxdy_auto_rdpt_amt": "익일자동상환금액",
        "bfdy_sll_amt": "전일매도금액",
        "thdt_sll_amt": "금일매도금액",
        "d2_auto_rdpt_amt": "D+2자동상환금액",
        "bfdy_tlex_amt": "전일제비용금액",
        "thdt_tlex_amt": "금일제비용금액",
        "tot_loan_amt": "총대출금액",
        "scts_evlu_amt": "유가증권평가금액",
        "tot_evlu_amt": "총평가금액",
        "nass_amt": "순자산금액",
        "fncg_gld_auto_rdpt_yn": "융자금자동상환여부",
        "pchs_amt_smtl_amt": "매입금액합계금액",
        "evlu_amt_smtl_amt": "평가금액합계금액",
        "evlu_pfls_smtl_amt": "평가손익합계금액",
        "tot_stln_slng_chgs": "총대주매각대금",
        "bfdy_tot_asst_evlu_amt": "전일총자산평가금액",
        "asst_icdc_amt": "자산증감금액",
        "asst_icdc_erng_rt": "자산증감수익률",
    }

    @classmethod
    def from_dict(cls, data: dict) -> "DomesticAccountSummary":
        """딕셔너리에서 DomesticAccountSummary 객체 생성."""
        return cls(
            dnca_tot_amt=Decimal(data["dnca_tot_amt"]),
            nxdy_excc_amt=Decimal(data["nxdy_excc_amt"]),
            prvs_rcdl_excc_amt=Decimal(data["prvs_rcdl_excc_amt"]),
            cma_evlu_amt=Decimal(data["cma_evlu_amt"]),
            bfdy_buy_amt=Decimal(data["bfdy_buy_amt"]),
            thdt_buy_amt=Decimal(data["thdt_buy_amt"]),
            nxdy_auto_rdpt_amt=Decimal(data["nxdy_auto_rdpt_amt"]),
            bfdy_sll_amt=Decimal(data["bfdy_sll_amt"]),
            thdt_sll_amt=Decimal(data["thdt_sll_amt"]),
            d2_auto_rdpt_amt=Decimal(data["d2_auto_rdpt_amt"]),
            bfdy_tlex_amt=Decimal(data["bfdy_tlex_amt"]),
            thdt_tlex_amt=Decimal(data["thdt_tlex_amt"]),
            tot_loan_amt=Decimal(data["tot_loan_amt"]),
            scts_evlu_amt=Decimal(data["scts_evlu_amt"]),
            tot_evlu_amt=Decimal(data["tot_evlu_amt"]),
            nass_amt=Decimal(data["nass_amt"]),
            fncg_gld_auto_rdpt_yn=data.get("fncg_gld_auto_rdpt_yn", ""),
            pchs_amt_smtl_amt=Decimal(data["pchs_amt_smtl_amt"]),
            evlu_amt_smtl_amt=Decimal(data["evlu_amt_smtl_amt"]),
            evlu_pfls_smtl_amt=Decimal(data["evlu_pfls_smtl_amt"]),
            tot_stln_slng_chgs=Decimal(data["tot_stln_slng_chgs"]),
            bfdy_tot_asst_evlu_amt=Decimal(data["bfdy_tot_asst_evlu_amt"]),
            asst_icdc_amt=Decimal(data["asst_icdc_amt"]),
            asst_icdc_erng_rt=Decimal(data["asst_icdc_erng_rt"]),
        )

    def to_korean(self) -> dict:
        """필드명을 한글로 변환한 딕셔너리 반환."""
        def format_value(v):
            if isinstance(v, Decimal):
                # 불필요한 소수점 이하 0 제거 후 천단위 구분자 적용
                normalized = v.normalize()
                if normalized == normalized.to_integral_value():
                    return f"{int(normalized):,}"
                return f"{normalized:,f}"
            return v
        
        return {
            self.FIELD_NAMES_KO.get(k, k): format_value(v)
            for k, v in self.__dict__.items()
            if v is not None
        }


@dataclass
class BalanceResponseBody(ResponseBody):
    ctx_area_fk100: str  # 연속조회검색조건100
    ctx_area_nk100: str  # 연속조회키100

    FIELD_NAMES_KO = {
        "rt_cd": "성공 실패 여부",
        "msg_cd": "응답코드",
        "msg1": "응답메세지",
        "ctx_area_fk100": "연속조회검색조건100",
        "ctx_area_nk100": "연속조회키100",
    }

    def to_korean(self) -> dict:
        """필드명을 한글로 변환한 딕셔너리 반환."""
        result = {}
        for k, v in self.__dict__.items():
            if v is None:
                continue
            key = self.FIELD_NAMES_KO.get(k, k)
            if isinstance(v, Decimal):
                result[key] = f"{v:,.2f}"
            else:
                result[key] = v
        return result

@dataclass
class DomesticBalanceResponse:
    """국내주식 잔고 조회 API 응답."""
    
    response_body: BalanceResponseBody
    balances: list[DomesticStockBalance] # 개별 종목 잔고 목록 (output1)
    summary: DomesticAccountSummary      # 계좌 요약 (output2)

    @property
    def is_success(self) -> bool:
        """API 호출 성공 여부."""
        return self.rt_cd == "0"

    @property
    def has_holdings(self) -> bool:
        """보유 종목 존재 여부."""
        return len(self.balances) > 0

    @classmethod
    def from_response(cls, data: dict) -> "DomesticBalanceResponse":
        """딕셔너리에서 DomesticBalanceResponse 객체 생성."""
        # output2는 리스트로 오지만 단일 요약 정보
        output2_data = data.get("output2", [])
        summary_data = output2_data[0] if output2_data else {}
        
        return cls(
            response_body=BalanceResponseBody(
                rt_cd=data["rt_cd"],
                msg_cd=data["msg_cd"],
                msg1=data["msg1"].strip(),
                ctx_area_fk100=data.get("ctx_area_fk100", "").strip(),
                ctx_area_nk100=data.get("ctx_area_nk100", "").strip()
            ),
            balances=[DomesticStockBalance.from_dict(item) for item in data.get("output1", [])],
            summary=DomesticAccountSummary.from_dict(summary_data) if summary_data else None,
        )


# =============================================================================
# 상품기본조회 [v1_국내주식-029]
# =============================================================================

@dataclass
class SearchInfo:
    """상품기본정보."""
    
    pdno: str              # 상품번호
    prdt_type_cd: str      # 상품유형코드
    prdt_name: str         # 상품명
    prdt_name120: str      # 상품명120
    prdt_abrv_name: str    # 상품약어명
    prdt_eng_name: str     # 상품영문명
    prdt_eng_name120: str  # 상품영문명120
    prdt_eng_abrv_name: str  # 상품영문약어명
    std_pdno: str          # 표준상품번호 (ISIN)
    shtn_pdno: str         # 단축상품번호 (종목코드)
    prdt_sale_stat_cd: str  # 상품판매상태코드
    prdt_risk_grad_cd: str  # 상품위험등급코드
    prdt_clsf_cd: str      # 상품분류코드
    prdt_clsf_name: str    # 상품분류명
    sale_strt_dt: Optional[str]  # 판매시작일
    sale_end_dt: Optional[str]   # 판매종료일
    wrap_asst_type_cd: str  # 랩자산유형코드
    ivst_prdt_type_cd: str  # 투자상품유형코드
    ivst_prdt_type_cd_name: str  # 투자상품유형코드명
    frst_erlm_dt: Optional[str]  # 최초등록일

    FIELD_NAMES_KO = {
        "pdno": "상품번호",
        "prdt_type_cd": "상품유형코드",
        "prdt_name": "상품명",
        "prdt_name120": "상품명120",
        "prdt_abrv_name": "상품약어명",
        "prdt_eng_name": "상품영문명",
        "prdt_eng_name120": "상품영문명120",
        "prdt_eng_abrv_name": "상품영문약어명",
        "std_pdno": "표준상품번호(ISIN)",
        "shtn_pdno": "종목코드",
        "prdt_sale_stat_cd": "상품판매상태코드",
        "prdt_risk_grad_cd": "상품위험등급코드",
        "prdt_clsf_cd": "상품분류코드",
        "prdt_clsf_name": "상품분류명",
        "sale_strt_dt": "판매시작일",
        "sale_end_dt": "판매종료일",
        "wrap_asst_type_cd": "랩자산유형코드",
        "ivst_prdt_type_cd": "투자상품유형코드",
        "ivst_prdt_type_cd_name": "투자상품유형코드명",
        "frst_erlm_dt": "최초등록일",
    }

    @classmethod
    def from_dict(cls, data: dict) -> "ProductBasicInfo":
        return cls(
            pdno=data["pdno"],
            prdt_type_cd=data["prdt_type_cd"],
            prdt_name=data["prdt_name"],
            prdt_name120=data["prdt_name120"],
            prdt_abrv_name=data["prdt_abrv_name"],
            prdt_eng_name=data["prdt_eng_name"],
            prdt_eng_name120=data["prdt_eng_name120"],
            prdt_eng_abrv_name=data["prdt_eng_abrv_name"],
            std_pdno=data["std_pdno"],
            shtn_pdno=data["shtn_pdno"],
            prdt_sale_stat_cd=data.get("prdt_sale_stat_cd", ""),
            prdt_risk_grad_cd=data.get("prdt_risk_grad_cd", ""),
            prdt_clsf_cd=data["prdt_clsf_cd"],
            prdt_clsf_name=data["prdt_clsf_name"],
            sale_strt_dt=data.get("sale_strt_dt") or None,
            sale_end_dt=data.get("sale_end_dt") or None,
            wrap_asst_type_cd=data["wrap_asst_type_cd"],
            ivst_prdt_type_cd=data["ivst_prdt_type_cd"],
            ivst_prdt_type_cd_name=data["ivst_prdt_type_cd_name"],
            frst_erlm_dt=data.get("frst_erlm_dt") or None,
        )

    def to_korean(self) -> dict:
        result = {}
        for k, v in self.__dict__.items():
            if v is None:
                continue
            key = self.FIELD_NAMES_KO.get(k, k)
            if isinstance(v, Decimal):
                result[key] = f"{v:,.2f}"
            else:
                result[key] = v
        return result


@dataclass
class SearchInfoResponse:
    """상품기본조회 API 응답."""
    
    response_body: ResponseBody
    info: Optional[SearchInfo]

    @property
    def is_success(self) -> bool:
        return self.rt_cd == "0"

    @classmethod
    def from_response(cls, data: dict) -> "SearchInfoResponse":
        output = data.get("output")
        return cls(
            response_body=ResponseBody(
                rt_cd=data["rt_cd"],
                msg_cd=data["msg_cd"],
                msg1=data["msg1"].strip()
            ),
            info=SearchInfo.from_dict(output) if output else None,
        )


# =============================================================================
# 주식기본조회 [v1_국내주식-067]
# =============================================================================

@dataclass
class SearchStockInfo:
    """주식기본정보."""
    
    pdno: str                # 상품번호
    prdt_type_cd: str        # 상품유형코드
    mket_id_cd: str          # 시장ID코드
    scty_grp_id_cd: str      # 증권그룹ID코드
    excg_dvsn_cd: str        # 거래소구분코드
    setl_mmdd: str           # 결산월일
    lstg_stqt: int           # 상장주수
    lstg_cptl_amt: Decimal   # 상장자본금액
    cpta: Decimal            # 자본금
    papr: Decimal            # 액면가
    issu_pric: Decimal       # 발행가
    kospi200_item_yn: str    # 코스피200종목여부
    scts_mket_lstg_dt: str   # 유가증권시장상장일자
    scts_mket_lstg_abol_dt: Optional[str]    # 유가증권시장상장폐지일자
    kosdaq_mket_lstg_dt: Optional[str]       # 코스닥시장상장일자
    kosdaq_mket_lstg_abol_dt: Optional[str]  # 코스닥시장상장폐지일자
    frbd_mket_lstg_dt: str                   # 프리보드시장상장일자
    frbd_mket_lstg_abol_dt: Optional[str]    # 프리보드시장상장폐지일자
    reits_kind_cd: str                       # 리츠종류코드
    etf_dvsn_cd: str                         # ETF구분코드
    oilf_fund_yn: str                        # 유전펀드여부
    idx_bztp_lcls_cd: str                    # 지수업종대분류코드
    idx_bztp_mcls_cd: str                    # 지수업종중분류코드
    idx_bztp_scls_cd: str                    # 지수업종소분류코드
    stck_kind_cd: str                        # 주식종류코드
    mfnd_opng_dt: Optional[str]              # 뮤추얼펀드개시일자
    mfnd_end_dt: Optional[str]               # 뮤추얼펀드종료일자
    dpsi_erlm_cncl_dt: Optional[str]         # 예탁등록취소일자
    etf_cu_qty: int                          # ETFCU수량
    prdt_name: str                           # 상품명
    prdt_name120: str                        # 상품명120
    prdt_abrv_name: str                      # 상품약어명
    std_pdno: str                            # 표준상품번호 (ISIN)
    prdt_eng_name: str                       # 상품영문명
    prdt_eng_name120: str                    # 상품영문명120
    prdt_eng_abrv_name: str                  # 상품영문약어명
    dpsi_aptm_erlm_yn: str                   # 예탁지정등록여부
    etf_txtn_type_cd: str                    # ETF과세유형코드
    etf_type_cd: str                         # ETF유형코드
    lstg_abol_dt: Optional[str]              # 상장폐지일
    nwst_odst_dvsn_cd: str                   # 신주구주구분코드
    sbst_pric: Decimal                       # 대용가격
    thco_sbst_pric: Decimal                  # 당사대용가격
    thco_sbst_pric_chng_dt: str              # 당사대용가격변경일자
    tr_stop_yn: str                          # 거래정지여부
    admn_item_yn: str                        # 관리종목여부
    thdt_clpr: Decimal                       # 당일종가
    bfdy_clpr: Decimal                       # 전일종가
    clpr_chng_dt: str                        # 종가변경일자
    std_idst_clsf_cd: str                    # 표준산업분류코드
    std_idst_clsf_cd_name: str               # 표준산업분류코드명
    idx_bztp_lcls_cd_name: str               # 지수업종대분류코드명
    idx_bztp_mcls_cd_name: str               # 지수업종중분류코드명
    idx_bztp_scls_cd_name: str               # 지수업종소분류코드명
    ocr_no: str                              # OCR번호
    crfd_item_yn: str                        # 크라우드펀딩종목여부
    elec_scty_yn: str                        # 전자증권여부
    issu_istt_cd: str                        # 발행기관코드
    etf_chas_erng_rt_dbnb: Decimal           # ETF추적수익율배수
    etf_etn_ivst_heed_item_yn: str           # ETFETN투자유의종목여부
    stln_int_rt_dvsn_cd: str                 # 대주이자율구분코드
    frnr_psnl_lmt_rt: Decimal                # 외국인개인한도비율
    lstg_rqsr_issu_istt_cd: str              # 상장신청인발행기관코드
    lstg_rqsr_item_cd: str                   # 상장신청인종목코드
    trst_istt_issu_istt_cd: str              # 신탁기관발행기관코드
    cptt_trad_tr_psbl_yn: str                # NXT 거래종목여부
    nxt_tr_stop_yn: str                      # NXT 거래정지여부

    FIELD_NAMES_KO = {
        "pdno": "상품번호",
        "prdt_type_cd": "상품유형코드",
        "mket_id_cd": "시장ID코드",
        "scty_grp_id_cd": "증권그룹ID코드",
        "excg_dvsn_cd": "거래소구분코드",
        "setl_mmdd": "결산월일",
        "lstg_stqt": "상장주수",
        "lstg_cptl_amt": "상장자본금액",
        "cpta": "자본금",
        "papr": "액면가",
        "issu_pric": "발행가",
        "kospi200_item_yn": "코스피200종목여부",
        "scts_mket_lstg_dt": "유가증권시장상장일자",
        "scts_mket_lstg_abol_dt": "유가증권시장상장폐지일자",
        "kosdaq_mket_lstg_dt": "코스닥시장상장일자",
        "kosdaq_mket_lstg_abol_dt": "코스닥시장상장폐지일자",
        "frbd_mket_lstg_dt": "프리보드시장상장일자",
        "frbd_mket_lstg_abol_dt": "프리보드시장상장폐지일자",
        "reits_kind_cd": "리츠종류코드",
        "etf_dvsn_cd": "ETF구분코드",
        "oilf_fund_yn": "유전펀드여부",
        "idx_bztp_lcls_cd": "지수업종대분류코드",
        "idx_bztp_mcls_cd": "지수업종중분류코드",
        "idx_bztp_scls_cd": "지수업종소분류코드",
        "stck_kind_cd": "주식종류코드",
        "mfnd_opng_dt": "뮤추얼펀드개시일자",
        "mfnd_end_dt": "뮤추얼펀드종료일자",
        "dpsi_erlm_cncl_dt": "예탁등록취소일자",
        "etf_cu_qty": "ETFCU수량",
        "prdt_name": "상품명",
        "prdt_name120": "상품명120",
        "prdt_abrv_name": "상품약어명",
        "std_pdno": "표준상품번호",
        "prdt_eng_name": "상품영문명",
        "prdt_eng_name120": "상품영문명120",
        "prdt_eng_abrv_name": "상품영문약어명",
        "dpsi_aptm_erlm_yn": "예탁지정등록여부",
        "etf_txtn_type_cd": "ETF과세유형코드",
        "etf_type_cd": "ETF유형코드",
        "lstg_abol_dt": "상장폐지일자",
        "nwst_odst_dvsn_cd": "신주구주구분코드",
        "sbst_pric": "대용가격",
        "thco_sbst_pric": "당사대용가격",
        "thco_sbst_pric_chng_dt": "당사대용가격변경일자",
        "tr_stop_yn": "거래정지여부",
        "admn_item_yn": "관리종목여부",
        "thdt_clpr": "당일종가",
        "bfdy_clpr": "전일종가",
        "clpr_chng_dt": "종가변경일자",
        "std_idst_clsf_cd": "표준산업분류코드",
        "std_idst_clsf_cd_name": "표준산업분류코드명",
        "idx_bztp_lcls_cd_name": "지수업종대분류코드명",
        "idx_bztp_mcls_cd_name": "지수업종중분류코드명",
        "idx_bztp_scls_cd_name": "지수업종소분류코드명",
        "ocr_no": "OCR번호",
        "crfd_item_yn": "크라우드펀딩종목여부",
        "elec_scty_yn": "전자증권여부",
        "issu_istt_cd": "발행기관코드",
        "etf_chas_erng_rt_dbnb": "ETF추적수익율배수",
        "etf_etn_ivst_heed_item_yn": "ETF/ETN투자유의종목여부",
        "stln_int_rt_dvsn_cd": "대주이자율구분코드",
        "frnr_psnl_lmt_rt": "외국인개인한도비율",
        "lstg_rqsr_issu_istt_cd": "상장신청인발행기관코드",
        "lstg_rqsr_item_cd": "상장신청인종목코드",
        "trst_istt_issu_istt_cd": "신탁기관발행기관코드",
        "cptt_trad_tr_psbl_yn": "NXT 거래종목여부",
        "nxt_tr_stop_yn": "NXT 거래정지여부",
    }

    @classmethod
    def from_dict(cls, data: dict) -> "StockBasicInfo":
        return cls(
            pdno=data["pdno"],
            prdt_type_cd=data["prdt_type_cd"],
            mket_id_cd=data["mket_id_cd"],
            scty_grp_id_cd=data["scty_grp_id_cd"],
            excg_dvsn_cd=data["excg_dvsn_cd"],
            setl_mmdd=data["setl_mmdd"],
            lstg_stqt=int(data["lstg_stqt"]),
            lstg_cptl_amt=Decimal(data["lstg_cptl_amt"]),
            cpta=Decimal(data["cpta"]),
            papr=Decimal(data["papr"]),
            issu_pric=Decimal(data["issu_pric"]),
            kospi200_item_yn=data["kospi200_item_yn"],
            scts_mket_lstg_dt=data["scts_mket_lstg_dt"],
            scts_mket_lstg_abol_dt=data.get("scts_mket_lstg_abol_dt") or None,
            kosdaq_mket_lstg_dt=data.get("kosdaq_mket_lstg_dt") or None,
            kosdaq_mket_lstg_abol_dt=data.get("kosdaq_mket_lstg_abol_dt") or None,
            frbd_mket_lstg_dt=data["frbd_mket_lstg_dt"],
            frbd_mket_lstg_abol_dt=data.get("frbd_mket_lstg_abol_dt") or None,
            reits_kind_cd=data.get("reits_kind_cd", ""),
            etf_dvsn_cd=data["etf_dvsn_cd"],
            oilf_fund_yn=data["oilf_fund_yn"],
            idx_bztp_lcls_cd=data["idx_bztp_lcls_cd"],
            idx_bztp_mcls_cd=data["idx_bztp_mcls_cd"],
            idx_bztp_scls_cd=data["idx_bztp_scls_cd"],
            stck_kind_cd=data["stck_kind_cd"],
            mfnd_opng_dt=data.get("mfnd_opng_dt") or None,
            mfnd_end_dt=data.get("mfnd_end_dt") or None,
            dpsi_erlm_cncl_dt=data.get("dpsi_erlm_cncl_dt") or None,
            etf_cu_qty=int(data["etf_cu_qty"]),
            prdt_name=data["prdt_name"],
            prdt_name120=data["prdt_name120"],
            prdt_abrv_name=data["prdt_abrv_name"],
            std_pdno=data["std_pdno"],
            prdt_eng_name=data["prdt_eng_name"],
            prdt_eng_name120=data["prdt_eng_name120"],
            prdt_eng_abrv_name=data["prdt_eng_abrv_name"],
            dpsi_aptm_erlm_yn=data["dpsi_aptm_erlm_yn"],
            etf_txtn_type_cd=data["etf_txtn_type_cd"],
            etf_type_cd=data.get("etf_type_cd", ""),
            lstg_abol_dt=data.get("lstg_abol_dt") or None,
            nwst_odst_dvsn_cd=data["nwst_odst_dvsn_cd"],
            sbst_pric=Decimal(data["sbst_pric"]),
            thco_sbst_pric=Decimal(data["thco_sbst_pric"]),
            thco_sbst_pric_chng_dt=data["thco_sbst_pric_chng_dt"],
            tr_stop_yn=data["tr_stop_yn"],
            admn_item_yn=data["admn_item_yn"],
            thdt_clpr=Decimal(data["thdt_clpr"]),
            bfdy_clpr=Decimal(data["bfdy_clpr"]),
            clpr_chng_dt=data["clpr_chng_dt"],
            std_idst_clsf_cd=data["std_idst_clsf_cd"],
            std_idst_clsf_cd_name=data["std_idst_clsf_cd_name"],
            idx_bztp_lcls_cd_name=data["idx_bztp_lcls_cd_name"],
            idx_bztp_mcls_cd_name=data["idx_bztp_mcls_cd_name"],
            idx_bztp_scls_cd_name=data["idx_bztp_scls_cd_name"],
            ocr_no=data["ocr_no"],
            crfd_item_yn=data.get("crfd_item_yn", ""),
            elec_scty_yn=data["elec_scty_yn"],
            issu_istt_cd=data["issu_istt_cd"],
            etf_chas_erng_rt_dbnb=Decimal(data["etf_chas_erng_rt_dbnb"]),
            etf_etn_ivst_heed_item_yn=data["etf_etn_ivst_heed_item_yn"],
            stln_int_rt_dvsn_cd=data["stln_int_rt_dvsn_cd"],
            frnr_psnl_lmt_rt=Decimal(data["frnr_psnl_lmt_rt"]),
            lstg_rqsr_issu_istt_cd=data.get("lstg_rqsr_issu_istt_cd", ""),
            lstg_rqsr_item_cd=data.get("lstg_rqsr_item_cd", ""),
            trst_istt_issu_istt_cd=data.get("trst_istt_issu_istt_cd", ""),
            nxt_tr_stop_yn=data["nxt_tr_stop_yn"],
            cptt_trad_tr_psbl_yn=data["cptt_trad_tr_psbl_yn"],
        )

    def to_korean(self) -> dict:
        result = {}
        for k, v in self.__dict__.items():
            if v is None:
                continue
            key = self.FIELD_NAMES_KO.get(k, k)
            if isinstance(v, Decimal):
                result[key] = f"{v:,.2f}"
            else:
                result[key] = v
        return result


@dataclass
class SearchStockInfoResponse:
    """주식기본조회 API 응답."""
    
    response_body: ResponseBody
    info: Optional[SearchStockInfo]

    @property
    def is_success(self) -> bool:
        return self.rt_cd == "0"

    @classmethod
    def from_response(cls, data: dict) -> "SearchStockInfoResponse":
        output = data.get("output")
        return cls(
            response_body=ResponseBody(
                rt_cd=data["rt_cd"],
                msg_cd=data["msg_cd"],
                msg1=data["msg1"].strip()
            ),
            info=SearchStockInfo.from_dict(output) if output else None,
        )