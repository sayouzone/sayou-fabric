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
class OverseasBalanceQueryParam:
    CANO: str               # 종합계좌번호
    ACNT_PRDT_CD: str       # 계좌상품코드
    OVRS_EXCG_CD: str       # 해외거래소코드
    TR_CRCY_CD: str         # 거래화폐코드

    OFL_YN: Optional[str] = None            # 오프라인여부
    CTX_AREA_FK200: Optional[str] = None    # 연속조회검색조건200
    CTX_AREA_NK200: Optional[str] = None    # 연속조회키200

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class OverseasStockBalance:
    """해외주식 개별 종목 잔고 정보."""
    
    cano: str            # 종합계좌번호
    acnt_prdt_cd: str    # 계좌상품코드
    prdt_type_cd: str    # 상품유형코드
    ovrs_pdno: str       # 해외상품번호 (종목코드)
    ovrs_item_name: str  # 해외종목명
    frcr_evlu_pfls_amt: Decimal  # 외화평가손익금액
    evlu_pfls_rt: Decimal    # 평가손익률
    pchs_avg_pric: Decimal   # 매입평균가격
    ovrs_cblc_qty: int       # 해외잔고수량
    ord_psbl_qty: int        # 주문가능수량
    frcr_pchs_amt1: Decimal  # 외화매입금액1
    ovrs_stck_evlu_amt: Decimal  # 해외주식평가금액
    now_pric2: Decimal       # 현재가격2
    tr_crcy_cd: str          # 거래통화코드
    ovrs_excg_cd: str        # 해외거래소코드
    loan_type_cd: str        # 대출유형코드
    loan_dt: Optional[str] = None  # 대출일자
    expd_dt: Optional[str] = None  # 만기일자

    FIELD_NAMES_KO = {
        "cano": "종합계좌번호",
        "acnt_prdt_cd": "계좌상품코드",
        "prdt_type_cd": "상품유형코드",
        "ovrs_pdno": "종목코드",
        "ovrs_item_name": "종목명",
        "frcr_evlu_pfls_amt": "외화평가손익금액",
        "evlu_pfls_rt": "평가손익률",
        "pchs_avg_pric": "매입평균가격",
        "ovrs_cblc_qty": "보유수량",
        "ord_psbl_qty": "주문가능수량",
        "frcr_pchs_amt1": "외화매입금액",
        "ovrs_stck_evlu_amt": "평가금액",
        "now_pric2": "현재가",
        "tr_crcy_cd": "거래통화코드",
        "ovrs_excg_cd": "거래소코드",
        "loan_type_cd": "대출유형코드",
        "loan_dt": "대출일자",
        "expd_dt": "만기일자",
    }

    @classmethod
    def from_dict(cls, data: dict) -> "OverseasStockBalance":
        """딕셔너리에서 OverseasStockBalance 객체 생성."""
        return cls(
            cano=data["cano"],
            acnt_prdt_cd=data["acnt_prdt_cd"],
            prdt_type_cd=data["prdt_type_cd"],
            ovrs_pdno=data["ovrs_pdno"],
            ovrs_item_name=data["ovrs_item_name"],
            frcr_evlu_pfls_amt=Decimal(data["frcr_evlu_pfls_amt"]),
            evlu_pfls_rt=Decimal(data["evlu_pfls_rt"]),
            pchs_avg_pric=Decimal(data["pchs_avg_pric"]),
            ovrs_cblc_qty=int(data["ovrs_cblc_qty"]),
            ord_psbl_qty=int(data["ord_psbl_qty"]),
            frcr_pchs_amt1=Decimal(data["frcr_pchs_amt1"]),
            ovrs_stck_evlu_amt=Decimal(data["ovrs_stck_evlu_amt"]),
            now_pric2=Decimal(data["now_pric2"]),
            tr_crcy_cd=data["tr_crcy_cd"],
            ovrs_excg_cd=data["ovrs_excg_cd"],
            loan_type_cd=data["loan_type_cd"],
            loan_dt=data.get("loan_dt") or None,
            expd_dt=data.get("expd_dt") or None,
        )

    def to_korean(self) -> dict:
        """필드명을 한글로 변환한 딕셔너리 반환."""
        def format_value(v):
            if isinstance(v, Decimal):
                # 불필요한 소수점 이하 0 제거 후 천단위 구분자 적용
                normalized = v.normalize()
                if normalized == normalized.to_integral_value():
                    return f"{int(normalized):,}"
                return f"{normalized:,.2f}"  # 소수점 이하 2자리까지 표시
            return v
        
        return {
            self.FIELD_NAMES_KO.get(k, k): format_value(v)
            for k, v in self.__dict__.items()
            if v is not None
        }


@dataclass
class OverseasBalanceSummary:
    """해외주식 잔고 요약 정보."""
    
    frcr_pchs_amt1: Decimal      # 외화매입금액합계
    ovrs_rlzt_pfls_amt: Decimal  # 해외실현손익금액
    ovrs_tot_pfls: Decimal       # 해외총손익
    rlzt_erng_rt: Decimal        # 실현수익률
    tot_evlu_pfls_amt: Decimal   # 총평가손익금액
    tot_pftrt: Decimal           # 총수익률
    frcr_buy_amt_smtl1: Decimal  # 외화매수금액소계1
    ovrs_rlzt_pfls_amt2: Decimal # 해외실현손익금액2
    frcr_buy_amt_smtl2: Decimal  # 외화매수금액소계2

    FIELD_NAMES_KO = {
        "frcr_pchs_amt1": "외화매입금액합계",
        "ovrs_rlzt_pfls_amt": "해외실현손익금액",
        "ovrs_tot_pfls": "해외총손익",
        "rlzt_erng_rt": "실현수익률",
        "tot_evlu_pfls_amt": "총평가손익금액",
        "tot_pftrt": "총수익률",
        "frcr_buy_amt_smtl1": "외화매수금액소계1",
        "ovrs_rlzt_pfls_amt2": "해외실현손익금액2",
        "frcr_buy_amt_smtl2": "외화매수금액소계2",
    }

    @classmethod
    def from_dict(cls, data: dict) -> "OverseasBalanceSummary":
        """딕셔너리에서 OverseasBalanceSummary 객체 생성."""
        return cls(
            frcr_pchs_amt1=Decimal(data["frcr_pchs_amt1"]),
            ovrs_rlzt_pfls_amt=Decimal(data["ovrs_rlzt_pfls_amt"]),
            ovrs_tot_pfls=Decimal(data["ovrs_tot_pfls"]),
            rlzt_erng_rt=Decimal(data["rlzt_erng_rt"]),
            tot_evlu_pfls_amt=Decimal(data["tot_evlu_pfls_amt"]),
            tot_pftrt=Decimal(data["tot_pftrt"]),
            frcr_buy_amt_smtl1=Decimal(data["frcr_buy_amt_smtl1"]),
            ovrs_rlzt_pfls_amt2=Decimal(data["ovrs_rlzt_pfls_amt2"]),
            frcr_buy_amt_smtl2=Decimal(data["frcr_buy_amt_smtl2"]),
        )

    def to_korean(self) -> dict:
        """필드명을 한글로 변환한 딕셔너리 반환."""
        def format_value(v):
            if isinstance(v, Decimal):
                # 불필요한 소수점 이하 0 제거 후 천단위 구분자 적용
                normalized = v.normalize()
                if normalized == normalized.to_integral_value():
                    return f"{int(normalized):,}"
                return f"{normalized:,.2f}"  # 소수점 이하 2자리까지 표시
            return v
        
        return {
            self.FIELD_NAMES_KO.get(k, k): format_value(v)
            for k, v in self.__dict__.items()
            if v is not None
        }


@dataclass
class BalanceResponseBody(ResponseBody):
    ctx_area_fk200: str  # 연속조회검색조건200
    ctx_area_nk200: str  # 연속조회키200

    FIELD_NAMES_KO = {
        "rt_cd": "성공 실패 여부",
        "msg_cd": "응답코드",
        "msg1": "응답메세지",
        "ctx_area_fk200": "연속조회검색조건200",
        "ctx_area_nk200": "연속조회키200",
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
class OverseasBalanceResponse:
    """해외주식 잔고 조회 API 응답."""
    
    response_body: BalanceResponseBody
    balances: list[OverseasStockBalance] # 개별 종목 잔고 목록
    summary: OverseasBalanceSummary      # 잔고 요약

    @property
    def is_success(self) -> bool:
        """API 호출 성공 여부."""
        return self.rt_cd == "0"

    @classmethod
    def from_response(cls, data: dict) -> "OverseasBalanceResponse":
        """딕셔너리에서 OverseasBalanceResponse 객체 생성."""
        return cls(
            response_body=BalanceResponseBody(
                rt_cd=data["rt_cd"],
                msg_cd=data["msg_cd"],
                msg1=data["msg1"].strip(),
                ctx_area_fk200=data.get("ctx_area_fk200", "").strip(),
                ctx_area_nk200=data.get("ctx_area_nk200", "").strip()
            ),
            balances=[OverseasStockBalance.from_dict(item) for item in data.get("output1", [])],
            summary=OverseasBalanceSummary.from_dict(data["output2"]),
        )
