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
Koreainvestment (KIS) 예탁원정보 Data Models
"""

@dataclass
class DividendInfo:
    """배당금 정보."""
    
    record_date: str          # 기준일 (YYYYMMDD)
    sht_cd: str               # 종목코드
    isin_name: str            # 종목명
    divi_kind: str            # 배당종류 (결산/분기)
    face_val: Decimal         # 액면가
    per_sto_divi_amt: Decimal # 현금배당금
    divi_rate: Decimal        # 배당현금배당률(%)
    stk_divi_rate: Decimal    # 주식배당률(%)
    divi_pay_dt: Optional[str]     # 배당금지급일
    stk_div_pay_dt: Optional[str]  # 주식배당지급일
    odd_pay_dt: Optional[str]      # 단수대금지급일
    stk_kind: str             # 주식종류 (보통/우선)
    high_divi_gb: str         # 고배당종목여부

    FIELD_NAMES_KO = {
        "record_date": "기준일",
        "sht_cd": "종목코드",
        "isin_name": "종목명",
        "divi_kind": "배당종류",
        "face_val": "액면가",
        "per_sto_divi_amt": "현금배당금",
        "divi_rate": "현금배당률(%)",
        "stk_divi_rate": "주식배당률(%)",
        "divi_pay_dt": "배당금지급일",
        "stk_div_pay_dt": "주식배당지급일",
        "odd_pay_dt": "단수대금지급일",
        "stk_kind": "주식종류",
        "high_divi_gb": "고배당종목여부",
    }

    @classmethod
    def from_dict(cls, data: dict) -> "DividendInfo":
        """딕셔너리에서 DividendInfo 객체 생성."""
        return cls(
            record_date=data["record_date"],
            sht_cd=data["sht_cd"],
            isin_name=data["isin_name"],
            divi_kind=data["divi_kind"],
            face_val=Decimal(data["face_val"]),
            per_sto_divi_amt=Decimal(data["per_sto_divi_amt"]),
            divi_rate=Decimal(data["divi_rate"]),
            stk_divi_rate=Decimal(data["stk_divi_rate"]),
            divi_pay_dt=data.get("divi_pay_dt") or None,
            stk_div_pay_dt=data.get("stk_div_pay_dt") or None,
            odd_pay_dt=data.get("odd_pay_dt") or None,
            stk_kind=data["stk_kind"],
            high_divi_gb=data.get("high_divi_gb", ""),
        )

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
class DividendResponse:
    """배당금 조회 API 응답."""
    
    response_body: ResponseBody
    dividends: list[DividendInfo]  # 배당금 목록

    @property
    def is_success(self) -> bool:
        """API 호출 성공 여부."""
        return self.rt_cd == "0"

    @classmethod
    def from_response(cls, data: dict) -> "DividendResponse":
        """딕셔너리에서 DividendResponse 객체 생성."""
        return cls(
            response_body=ResponseBody(
                rt_cd=data["rt_cd"],
                msg_cd=data["msg_cd"],
                msg1=data["msg1"].strip()
            ),
            dividends=[DividendInfo.from_dict(item) for item in data.get("output1", [])],
        )