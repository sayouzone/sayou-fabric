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

class ExchangeCode(str, Enum):
    """해외거래소코드"""
    ALL = "%"       # 전종목
    NASD = "NASD"   # 나스닥
    NYSE = "NYSE"   # 뉴욕
    AMEX = "AMEX"   # 아멕스
    SEHK = "SEHK"   # 홍콩
    SHAA = "SHAA"   # 중국상해
    SZAA = "SZAA"   # 중국심천
    TKSE = "TKSE"   # 일본
    HASE = "HASE"   # 베트남하노이
    VNSE = "VNSE"   # 베트남호치민


class CurrencyCode(str, Enum):
    """통화코드"""
    USD = "USD"     # 미국달러
    HKD = "HKD"     # 홍콩달러
    CNY = "CNY"     # 중국위안
    JPY = "JPY"     # 일본엔
    VND = "VND"     # 베트남동


class OrderDivision(str, Enum):
    """주문구분"""
    LIMIT = "00"            # 지정가
    MARKET = "01"           # 시장가
    LOC = "02"              # LOC (장마감지정가)
    MOC = "03"              # MOC (장마감시장가)
    EXTENDED_LIMIT = "05"   # 장전시간외지정가
    EXTENDED_MARKET = "06"  # 장후시간외지정가


class RevisionCancelCode(str, Enum):
    """정정취소구분코드"""
    REVISION = "01"     # 정정
    CANCEL = "02"       # 취소


class OverseasTrId(str, Enum):
    """해외주식 거래ID"""
    BUY = "TTTT1002U"           # 매수
    SELL = "TTTT1006U"          # 매도
    REVISION_CANCEL = "TTTT1004U"   # 정정취소
    CONCLUSION_LIST = "TTTS3035R"   # 주문체결내역


@dataclass
class OverseasOrderParam:
    """해외주식 주문 요청 파라미터"""
    CANO: str                   # 종합계좌번호 (8자리)
    ACNT_PRDT_CD: str           # 계좌상품코드 (2자리)
    OVRS_EXCG_CD: str           # 해외거래소코드
    PDNO: str                   # 종목코드
    ORD_QTY: str                # 주문수량
    OVRS_ORD_UNPR: str          # 해외주문단가
    ORD_SVR_DVSN_CD: str = "0"  # 주문서버구분코드
    ORD_DVSN: str = "00"        # 주문구분 (00: 지정가)

    CTAC_TLNO: Optional[str] = None         # 연락전화번호
    MGCO_APTM_ODNO: Optional[str] = None    # 운용사지정주문번호
    SLL_TYPE: Optional[str] = None          # 판매유형
    START_TIME: Optional[str] = None        # 시작시간
    END_TIME: Optional[str] = None          # 종료시간
    ALGO_ORD_TMD_DVSN_CD: Optional[str] = None   # 알고리즘주문시간구분코드

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}

    @classmethod
    def create(
        cls,
        account_number: str,
        product_code: str,
        stock_code: str,
        quantity: int,
        price: float,
        exchange: ExchangeCode | str = ExchangeCode.NASD,
        order_division: OrderDivision | str = OrderDivision.LIMIT,
    ) -> "OverseasOrderParam":
        """팩토리 메서드로 주문 파라미터 생성"""
        return cls(
            CANO=account_number,
            ACNT_PRDT_CD=product_code,
            OVRS_EXCG_CD=exchange.value if isinstance(exchange, ExchangeCode) else exchange,
            PDNO=stock_code,
            ORD_QTY=str(quantity),
            OVRS_ORD_UNPR=str(price),
            ORD_DVSN=order_division.value if isinstance(order_division, OrderDivision) else order_division,
        )


@dataclass
class OverseasRevisionCancelParam:
    """해외주식 정정취소 요청 파라미터"""
    CANO: str                   # 종합계좌번호 (8자리)
    ACNT_PRDT_CD: str           # 계좌상품코드 (2자리)
    OVRS_EXCG_CD: str           # 해외거래소코드
    PDNO: str                   # 상품번호
    ORGN_ODNO: str              # 원주문번호
    RVSE_CNCL_DVSN_CD: str      # 정정취소구분코드
    ORD_QTY: str                # 주문수량
    OVRS_ORD_UNPR: str          # 해외주문단가
    ORD_SVR_DVSN_CD: str = "0"  # 주문서버구분코드

    MGCO_APTM_ODNO: Optional[str] = None    # 운용사지정주문번호

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}

    @classmethod
    def create_revision(
        cls,
        account_number: str,
        product_code: str,
        stock_code: str,
        order_no: str,
        quantity: int,
        price: float,
        exchange: ExchangeCode | str = ExchangeCode.NASD,
    ) -> "OverseasRevisionCancelParam":
        """정정 주문 파라미터 생성"""
        return cls(
            CANO=account_number,
            ACNT_PRDT_CD=product_code,
            OVRS_EXCG_CD=exchange.value if isinstance(exchange, ExchangeCode) else exchange,
            PDNO=stock_code,
            ORGN_ODNO=order_no,
            RVSE_CNCL_DVSN_CD=RevisionCancelCode.REVISION.value,
            ORD_QTY=str(quantity),
            OVRS_ORD_UNPR=str(price),
        )

    @classmethod
    def create_cancel(
        cls,
        account_number: str,
        product_code: str,
        stock_code: str,
        order_no: str,
        quantity: int,
        exchange: ExchangeCode | str = ExchangeCode.NASD,
    ) -> "OverseasRevisionCancelParam":
        """취소 주문 파라미터 생성"""
        return cls(
            CANO=account_number,
            ACNT_PRDT_CD=product_code,
            OVRS_EXCG_CD=exchange.value if isinstance(exchange, ExchangeCode) else exchange,
            PDNO=stock_code,
            ORGN_ODNO=order_no,
            RVSE_CNCL_DVSN_CD=RevisionCancelCode.CANCEL.value,
            ORD_QTY=str(quantity),
            OVRS_ORD_UNPR="0",
        )

@dataclass
class OverseasConclusionListParam:
    """해외주식 주문 요청 파라미터"""
    CANO: str                   # 종합계좌번호 (8자리)
    ACNT_PRDT_CD: str           # 계좌상품코드 (2자리)
    PDNO: str                   # 상품번호, 전종목일 경우 "%" 입력
    ORD_STRT_DT: str            # 주문시작일자, YYYYMMDD 형식 (현지시각 기준)
    ORD_END_DT: str             # 주문종료일자, YYYYMMDD 형식 (현지시각 기준)
    SLL_BUY_DVSN: str = "00"    # 매도매수구분, 00 : 전체, 01 : 매도, 02 : 매수
    CCLD_NCCS_DVSN: str = "00"  # 체결미체결구분, 00 : 전체, 01 : 체결, 02 : 미체결
    OVRS_EXCG_CD: str = "%"     # 해외거래소코드, 전종목일 경우 "%" 입력
    SORT_SQN: str = "AS"        # 정렬순서, DS : 정순, AS : 역순
    ORD_DT: str = ""          # 주문일자, YYYYMMDD 형식 (현지시각 기준), Null 값 설정
    ORD_GNO_BRNO: str =""    # 주문채번지점번호, 5자리, Null 값 설정
    ODNO: str = ""            # 주문번호, Null 값 설정
    CTX_AREA_NK200: str = ""    # 연속조회키200, 공란 : 최초 조회시, 이전 조회 Output CTX_AREA_NK200값 : 다음페이지 조회시(2번째부터)
    CTX_AREA_FK200: str = ""    # 연속조회검색조건200, 공란 : 최초 조회시, 이전 조회 Output CTX_AREA_FK200값 : 다음페이지 조회시(2번째부터)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}

    @classmethod
    def create(
        cls,
        account_number: str,
        product_code: str,
        stock_code: str,
        start_date: str,
        end_date: str,
        exchange: ExchangeCode | str = ExchangeCode.ALL,
    ) -> "OverseasConclusionListParam":
        """팩토리 메서드로 주문 파라미터 생성"""
        return cls(
            CANO=account_number,
            ACNT_PRDT_CD=product_code,
            OVRS_EXCG_CD=exchange.value if isinstance(exchange, ExchangeCode) else exchange,
            PDNO=stock_code,
            ORD_STRT_DT=start_date,
            ORD_END_DT=end_date,
        )

@dataclass
class OverseasOrderOutput:
    """해외주식 주문 응답 output"""
    KRX_FWDG_ORD_ORGNO: str      # 한국거래소전송주문조직번호
    ODNO: str                    # 주문번호
    ORD_TMD: str                 # 주문시각

    FIELD_NAMES_KO = {
        "KRX_FWDG_ORD_ORGNO": "한국거래소전송주문조직번호",
        "ODNO": "주문번호",
        "ORD_TMD": "주문시각",
    }

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

    @classmethod
    def from_dict(cls, data: dict) -> "OverseasOrderOutput":
        return cls(
            KRX_FWDG_ORD_ORGNO=data.get("KRX_FWDG_ORD_ORGNO", ""),
            ODNO=data.get("ODNO", ""),
            ORD_TMD=data.get("ORD_TMD", ""),
        )


@dataclass
class OverseasOrderResponse:
    """해외주식 주문 응답"""
    response_body: ResponseBody
    order: Optional[OverseasOrderOutput]   # 응답상세

    @property
    def is_success(self) -> bool:
        return self.response_body.rt_cd == "0"

    @property
    def order_no(self) -> str:
        """주문번호 반환"""
        return self.output.ODNO if self.output else ""

    @classmethod
    def from_response(cls, data: dict) -> "OverseasOrderResponse":
        output_data = data.get("output")
        output = OverseasOrderOutput.from_dict(output_data) if output_data else None

        return cls(
            response_body=ResponseBody(
                rt_cd=data["rt_cd"],
                msg_cd=data["msg_cd"],
                msg1=data["msg1"].strip()
            ),
            order=output,
        )

@dataclass
class OverseasResponseBody(ResponseBody):
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
class OverseasConclusionList:
    """해외주식 주문체결내역"""

    ord_dt: str    # 주문일자
    ord_gno_brno: str    # 주문채번지점번호
    odno: str    # 주문번호
    orgn_odno: str    # 원주문번호
    sll_buy_dvsn_cd: str    # 매도매수구분코드
    sll_buy_dvsn_cd_name: str    # 매도매수구분코드명
    rvse_cncl_dvsn: str    # 정정취소구분
    rvse_cncl_dvsn_name: str    # 정정취소구분명
    pdno: str    # 상품번호
    prdt_name: str    # 상품명
    ft_ord_qty: str    # FT주문수량
    ft_ord_unpr3: str    # FT주문단가3
    ft_ccld_qty: str    # FT체결수량
    ft_ccld_unpr3: str    # FT체결단가3
    ft_ccld_amt3: str    # FT체결금액3
    nccs_qty: str    # 미체결수량
    prcs_stat_name: str    # 처리상태명
    rjct_rson: str    # 거부사유
    rjct_rson_name: str    # 거부사유명
    ord_tmd: str    # 주문시각
    tr_mket_name: str    # 거래시장명
    tr_natn: str    # 거래국가
    tr_natn_name: str    # 거래국가명
    ovrs_excg_cd: str    # 해외거래소코드
    tr_crcy_cd: str    # 거래통화코드
    dmst_ord_dt: str    # 국내주문일자
    thco_ord_tmd: str    # 당사주문시각
    loan_type_cd: str    # 대출유형코드
    loan_dt: str    # 대출일자
    mdia_dvsn_name: str    # 매체구분명
    usa_amk_exts_rqst_yn: str    # 미국애프터마켓연장신청여부
    splt_buy_attr_name: str    # 분할매수/매도속성명

    FIELD_NAMES_KO = {
        "ord_dt": "주문일자",
        "ord_gno_brno": "주문채번지점번호",
        "odno": "주문번호",
        "orgn_odno": "원주문번호",
        "sll_buy_dvsn_cd": "매도매수구분코드",
        "sll_buy_dvsn_cd_name": "매도매수구분코드명",
        "rvse_cncl_dvsn": "정정취소구분",
        "rvse_cncl_dvsn_name": "정정취소구분명",
        "pdno": "상품번호",
        "prdt_name": "상품명",
        "ft_ord_qty": "FT주문수량",
        "ft_ord_unpr3": "FT주문단가3",
        "ft_ccld_qty": "FT체결수량",
        "ft_ccld_unpr3": "FT체결단가3",
        "ft_ccld_amt3": "FT체결금액3",
        "nccs_qty": "미체결수량",
        "prcs_stat_name": "처리상태명",
        "rjct_rson": "거부사유",
        "rjct_rson_name": "거부사유명",
        "ord_tmd": "주문시각",
        "tr_mket_name": "거래시장명",
        "tr_natn": "거래국가",
        "tr_natn_name": "거래국가명",
        "ovrs_excg_cd": "해외거래소코드",
        "tr_crcy_cd": "거래통화코드",
        "dmst_ord_dt": "국내주문일자",
        "thco_ord_tmd": "당사주문시각",
        "loan_type_cd": "대출유형코드",
        "loan_dt": "대출일자",
        "mdia_dvsn_name": "매체구분명",
        "usa_amk_exts_rqst_yn": "미국애프터마켓연장신청여부",
        "splt_buy_attr_name": "분할매수/매도속성명",
    }

    @classmethod
    def from_dict(cls, data: dict) -> "OverseasConclusionList":
        """딕셔너리에서 OverseasConclusionList 객체 생성."""
        return cls(
            ord_dt=data["ord_dt"],
            ord_gno_brno=data["ord_gno_brno"],
            odno=data["odno"],
            orgn_odno=data["orgn_odno"],
            sll_buy_dvsn_cd=data["sll_buy_dvsn_cd"],
            sll_buy_dvsn_cd_name=data["sll_buy_dvsn_cd_name"],
            rvse_cncl_dvsn=data["rvse_cncl_dvsn"],
            rvse_cncl_dvsn_name=data["rvse_cncl_dvsn_name"],
            pdno=data["pdno"],
            prdt_name=data["prdt_name"],
            ft_ord_qty=data["ft_ord_qty"],
            ft_ord_unpr3=data["ft_ord_unpr3"],
            ft_ccld_qty=data["ft_ccld_qty"],
            ft_ccld_unpr3=data["ft_ccld_unpr3"],
            ft_ccld_amt3=data["ft_ccld_amt3"],
            nccs_qty=data["nccs_qty"],
            prcs_stat_name=data["prcs_stat_name"],
            rjct_rson=data["rjct_rson"],
            rjct_rson_name=data["rjct_rson_name"],
            ord_tmd=data["ord_tmd"],
            tr_mket_name=data["tr_mket_name"],
            tr_natn=data["tr_natn"],
            tr_natn_name=data["tr_natn_name"],
            ovrs_excg_cd=data["ovrs_excg_cd"],
            tr_crcy_cd=data["tr_crcy_cd"],
            dmst_ord_dt=data["dmst_ord_dt"],
            thco_ord_tmd=data["thco_ord_tmd"],
            loan_type_cd=data["loan_type_cd"],
            loan_dt=data["loan_dt"],
            mdia_dvsn_name=data["mdia_dvsn_name"],
            usa_amk_exts_rqst_yn=data["usa_amk_exts_rqst_yn"],
            splt_buy_attr_name=data["splt_buy_attr_name"],
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
class OverseasConclusionListResponse:
    """해외주식 주문체결내역 조회 응답"""

    response_body: OverseasResponseBody
    conclusions: list[OverseasConclusionList] # 개별 종목 잔고 목록

    @property
    def is_success(self) -> bool:
        """API 호출 성공 여부."""
        return self.rt_cd == "0"

    @classmethod
    def from_response(cls, data: dict) -> "OverseasConclusionListResponse":
        """딕셔너리에서 OverseasConclusionListResponse 객체 생성."""
        return cls(
            response_body=OverseasResponseBody(
                rt_cd=data["rt_cd"],
                msg_cd=data["msg_cd"],
                msg1=data["msg1"].strip(),
                ctx_area_fk200=data.get("ctx_area_fk200", "").strip(),
                ctx_area_nk200=data.get("ctx_area_nk200", "").strip()
            ),
            conclusions=[OverseasConclusionList.from_dict(item) for item in data.get("output", [])],
        )