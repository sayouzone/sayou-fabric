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
import os
import pandas as pd
import requests

from datetime import datetime
from io import StringIO
from lxml import html
from typing import Optional

from ..client import KoreainvestmentClient
from ..models.base_model import (
    AccountConfig,
    RequestHeader,
)
from ..models.overseas import (
    OverseasBalanceQueryParam,
    OverseasBalanceResponse,
)
from .html_extractor import HtmlTableExtractor
from ..utils.token_manager import TokenManager
from ..utils.storage import FileStorage
from ..utils.utils import (
    KIS_OPENAPI_PROD,
    KIS_OPENAPI_OPS,
    get_filename,
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OverseasParser:
    """KIS 해외 데이터를 파싱하는 클래스"""

    DEFAULT_LOCAL_PATH = './config'

    def __init__(
        self,
        client: KoreainvestmentClient,
        local_path: Optional[str] = None,
    ):
        self._client = client

        self._account = AccountConfig(
            account_number="72749154",
            product_code="01",
        )
        self._token_manager = TokenManager(client)
        self._extractor = HtmlTableExtractor()
        self._storage = FileStorage(local_path or self.DEFAULT_LOCAL_PATH)
    
    def inquire_balance(self) -> OverseasBalanceResponse:
        """
        주식잔고조회

        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/overseas-stock/v1/trading/inquire-balance
        """
        url = KIS_OPENAPI_PROD + "/uapi/overseas-stock/v1/trading/inquire-balance"

        headers = self._build_headers(tr_id="TTTS3012R")
        params = OverseasBalanceQueryParam(
            CANO=self._account.CANO,
            ACNT_PRDT_CD=self._account.ACNT_PRDT_CD,
            OVRS_EXCG_CD="NASD",
            TR_CRCY_CD="USD",
            CTX_AREA_FK200="",
            CTX_AREA_NK200="",
            OFL_YN="",
        )

        logger.debug(f"Request URL: {url}")
        logger.debug(f"Request Headers: {headers.to_dict()}")
        logger.debug(f"Request Params: {params.to_dict()}")

        response = self._client._get(
            url,
            params=params.to_dict(),
            headers=headers.to_dict(),
        )

        if response.status_code != 200:
            self._handle_error(response)

        return OverseasBalanceResponse.from_response(response.json())

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
        
