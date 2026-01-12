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
from ..models import (
    OverseasTradingResponse,
)
from ..utils.token_manager import TokenManager
from ..utils.utils import (
    KIS_OPENAPI_PROD,
    KIS_OPENAPI_OPS,
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OverseasTradingParser:
    """KIS 해외 데이터를 파싱하는 클래스"""

    def __init__(
        self,
        client: KoreainvestmentClient,
    ):
        self._client = client

        self._account = AccountConfig(
            account_number="72749154",
            product_code="01",
        )
        self._token_manager = TokenManager(client)
    
    def buy_stock(self, stock_code: str, order_quantity: int, order_price: float, exchange_code: str = "NASD"):
        tr_id = "TTTT1002U"
        currency_code = "USD"

        return self.order(stock_code, order_quantity, order_price, tr_id, exchange_code, currency_code)
    
    def sell_stock(self, stock_code: str, order_quantity: int, order_price: float, exchange_code: str = "NASD"):
        tr_id = "TTTT1006U"
        currency_code = "USD"

        return self.order(stock_code, order_quantity, order_price, tr_id, exchange_code, currency_code)

    def order(
        self,
        stock_code: str,
        order_quantity: int,
        order_price: float,
        tr_id: str = "TTTT1002U",
        exchange_code: str = "NASD",
        currency_code: str = "USD",
    ):
        """
        해외주식 주문[v1_해외주식-001]

        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/overseas-stock/v1/trading/order
        """
        url = KIS_OPENAPI_PROD + "/uapi/overseas-stock/v1/trading/order"

        headers = self._build_headers(tr_id=tr_id)
        params = {
            "CANO": self._account.CANO,
            "ACNT_PRDT_CD": self._account.ACNT_PRDT_CD,
            "OVRS_EXCG_CD": exchange_code,
            "PDNO": stock_code,
            "ORD_QTY": str(order_quantity),
            "OVRS_ORD_UNPR": str(order_price),
            "ORD_SVR_DVSN_CD": "0",
            "ORD_DVSN": "00",
        }
        logger.debug(f"Request URL: {url}")
        logger.debug(f"Request Headers: {headers.to_dict()}")
        logger.debug(f"Request Params: {params}")

        response = self._client._post(url, json=params, headers=headers.to_dict())
        #response = requests.post(url, json=params, headers=headers.to_dict())

        if response.status_code != 200:
            self._handle_error(response)

        return OverseasTradingResponse.from_response(response.json())

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
        
