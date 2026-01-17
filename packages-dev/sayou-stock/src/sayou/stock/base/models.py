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

from dataclasses import dataclass
from typing import Optional

@dataclass
class BaseRequestHeader:
    """API 요청 헤더 데이터 클래스"""

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}

@dataclass
class BaseResponseBody:
    """응답 body."""
    
    FIELD_NAMES_KO = {
        #"example": "예제",
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

    @classmethod
    def from_response(cls, response_data: dict) -> "BaseResponseBody":
        """API 응답으로부터 AccessToken 생성"""
        return cls(**response_data)