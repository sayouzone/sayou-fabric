# Copyright (c) 2025-2026, Sayouzone
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

import logging
from typing import Optional

from ..client import KoreainvestmentClient
from ..models import (
    RequestHeader,
    DividendInfo,
    DividendResponse,
)
from ..utils.token_manager import TokenManager
from ..utils.utils import (
    KIS_OPENAPI_PROD,
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DomesticKsdinfoParser:
    """KIS 국내 예탁원정보 데이터를 파싱하는 클래스"""

    def __init__(
        self,
        client: KoreainvestmentClient,
    ):
        self._client = client
        self._token_manager = TokenManager(client)

    def dividend(self, stock_code: str) -> dict:
        """
        예탁원정보(배당일정)[국내주식-145]
        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/ksdinfo/dividend
        """
        url = KIS_OPENAPI_PROD + "/uapi/domestic-stock/v1/ksdinfo/dividend"

        headers = self._build_headers(tr_id="HHKDB669102C0")
        params = {
            "CTS": "",
            "GB1": "0",
            "F_DT": "20250101",
            "T_DT": "20251231",
            "SHT_CD": stock_code,
            "HIGH_GB": "",
        }

        response = self._client._get(url, params=params, headers=headers.to_dict())

        if response.status_code != 200:
            self._handle_error(response)

        return DividendResponse.from_response(response.json())

    def _build_headers(self, tr_id: str, **kwargs) -> RequestHeader:
        """공통 헤더 생성"""
        return RequestHeader(
            authorization=self._token_manager.authorization,
            appkey=self._client.app_key,
            appsecret=self._client.app_secret,
            tr_id=tr_id,
            content_type="application/json; charset=utf-8",
            **kwargs,
        )

    def _handle_error(self, response) -> None:
        """에러 응답 처리"""
        try:
            error_data = response.json()
            rt_cd = error_data.get("rt_cd")
            msg_cd = error_data.get("msg_cd")
            msg1 = error_data.get("msg1")
            logger.error(f"API Error - rt_cd: {rt_cd}, msg_cd: {msg_cd}, msg: {msg1}")
            raise Exception(f"API Error [{msg_cd}]: {msg1}")
        except ValueError:
            logger.error(f"HTTP Error: {response.status_code} - {response.content}")
            raise Exception(f"HTTP Error: {response.status_code}")
        
