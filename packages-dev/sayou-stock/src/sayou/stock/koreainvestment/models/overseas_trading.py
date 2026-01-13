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