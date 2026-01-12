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

"""
Koreainvestment (KIS) Data Models
"""

#계좌번호 앞 8자리
my_acct_stock: "증권계좌 8자리"
my_acct_future: "선물옵션계좌 8자리"
my_paper_stock: "모의투자 증권계좌 8자리"
my_paper_future: "모의투자 선물옵션계좌 8자리"

class BankAccountType(Enum):
    """계좌 유형 열거형(계좌번호 뒤 2자리)"""
    INTERGRATED = "01"            # 종합계좌
    DOMESTIC_FUTURE_OPTION = "03" # 국내선물옵션계좌
    OVERSEAS_FUTURE_OPTION = "08" # 해외선물옵션 계좌
    INDIVIDUAL_PENSION = "22"     # 개인연금
    RETIREMENT_PENSION = "29"     # 퇴직연금

@dataclass
class AccountConfig:
    """계좌 설정 데이터 클래스"""
    account_number: str            # 종합계좌번호 (8자리)
    product_code: BankAccountType  # 계좌상품코드 (2자리)

    @property
    def CANO(self) -> str:
        """종합계좌번호 반환"""
        return self.account_number

    @property
    def ACNT_PRDT_CD(self) -> str:
        """계좌상품코드 반환"""
        return self.product_code

@dataclass
class AccessToken:
    """액세스 토큰 데이터 클래스"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 86400
    expired_at: Optional[str] = None

    @property
    def is_expired(self) -> bool:
        """토큰 만료 여부 확인"""
        if not self.expired_at:
            return True
        return self.expired_at < datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @property
    def authorization(self) -> str:
        """Authorization 헤더 값 반환"""
        return f"{self.token_type} {self.access_token}"

    @classmethod
    def from_response(cls, response_data: dict) -> "AccessToken":
        """API 응답으로부터 AccessToken 생성"""
        return cls(
            access_token=response_data.get("access_token", ""),
            token_type=response_data.get("token_type", "Bearer"),
            expires_in=response_data.get("expires_in", 86400),
            expired_at=response_data.get("access_token_token_expired"),
        )

    def to_bytes(self) -> bytes:
        return json.dumps(self.to_dict()).encode("utf-8")

    @classmethod
    def from_bytes(cls, token_bytes: bytes) -> "AccessToken":
        token_dict = json.loads(token_bytes.decode("utf-8"))
        return cls.from_response(token_dict)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}

@dataclass
class RequestHeader:
    """API 요청 헤더 데이터 클래스"""
    # 필수 필드
    authorization: str      # 접근토큰
    appkey: str             # 앱키
    appsecret: str          # 앱시크릿키
    tr_id: str              # 거래ID

    # 선택 필드
    content_type: Optional[str] = None      # 컨텐츠타입
    personalseckey: Optional[str] = None    # 고객식별키
    tr_cont: Optional[str] = None           # 연속 거래 여부
    custtype: Optional[str] = None          # 고객타입
    seq_no: Optional[str] = None            # 일련번호
    mac_address: Optional[str] = None       # 맥주소
    phone_number: Optional[str] = None      # 핸드폰번호
    ip_addr: Optional[str] = None           # 접속 단말 공인 IP
    gt_uid: Optional[str] = None            # Global UID

    def to_dict(self) -> dict:
        result = {}
        for k, v in self.__dict__.items():
            if v is not None:
                # content_type을 content-type으로 변환
                key = k.replace('_', '-') if k == 'content_type' else k
                result[key] = v
        return result

@dataclass
class ResponseBody:
    """응답 body."""
    
    rt_cd: str
    msg_cd: str
    msg1: str

    FIELD_NAMES_KO = {
        "rt_cd": "성공 실패 여부",
        "msg_cd": "응답코드",
        "msg1": "응답메세지",
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
