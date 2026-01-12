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
class OverseasTradingParam:
    CANO: str               # 종합계좌번호
    ACNT_PRDT_CD: str       # 계좌상품코드
    OVRS_EXCG_CD: str       # 해외거래소코드
    PDNO: str               # 상품번호
    ORD_QTY: str            # 주문수량
    OVRS_ORD_UNPR: str      # 해외주문단가
    ORD_SVR_DVSN_CD: str    # 주문서버구분코드
    ORD_DVSN: str           # 주문구분
    
    CTAC_TLNO: Optional[str] = None             # 연락전화번호
    MGCO_APTM_ODNO: Optional[str] = None        # 운용사지정주문번호
    SLL_TYPE: Optional[str] = None              # 판매유형
    START_TIME: Optional[str] = None            # 시작시간
    END_TIME: Optional[str] = None              # 종료시간
    ALGO_ORD_TMD_DVSN_CD: Optional[str] = None  # 알고리즘주문시간구분코드
    
    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}

@dataclass
class OverseasTrading:
    """해외주식 주문[v1_해외주식-001] 정보."""
    
    KRX_FWDG_ORD_ORGNO: str      # 한국거래소전송주문조직번호
    ODNO: str                    # 주문번호
    ORD_TMD: str                 # 주문시각

    FIELD_NAMES_KO = {
        "KRX_FWDG_ORD_ORGNO": "한국거래소전송주문조직번호",
        "ODNO": "주문번호",
        "ORD_TMD": "주문시각",
    }

    @classmethod
    def from_dict(cls, data: dict) -> "OverseasTrading":
        """딕셔너리에서 OverseasTrading 객체 생성."""
        return cls(
            KRX_FWDG_ORD_ORGNO=data["KRX_FWDG_ORD_ORGNO"],
            ODNO=data["ODNO"],
            ORD_TMD=data["ORD_TMD"],
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
class OverseasTradingResponse:
    """해외주식 주문[v1_해외주식-001] 응답."""
    
    response_body: ResponseBody
    trading: OverseasTrading

    @property
    def is_success(self) -> bool:
        """API 호출 성공 여부."""
        return self.rt_cd == "0"

    @classmethod
    def from_response(cls, data: dict) -> "OverseasTradingResponse":
        """딕셔너리에서 OverseasTradingResponse 객체 생성."""
        return cls(
            response_body=ResponseBody(
                rt_cd=data["rt_cd"],
                msg_cd=data["msg_cd"],
                msg1=data["msg1"].strip()
            ),
            trading=OverseasTrading.from_dict(data["output"]),
        )
