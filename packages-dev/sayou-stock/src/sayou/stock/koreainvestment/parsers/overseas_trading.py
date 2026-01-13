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
    ExchangeCode,
    OverseasTrId,
    OverseasOrderParam,
    OverseasRevisionCancelParam,
    OverseasOrderResponse,
)
from ..utils.token_manager import TokenManager
from ..utils.utils import (
    KIS_OPENAPI_PROD,
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OverseasTradingParser:
    """KIS 해외주식 주문을 처리하는 클래스"""

    ORDER_URL = KIS_OPENAPI_PROD + "/uapi/overseas-stock/v1/trading/order"
    REVISION_CANCEL_URL = KIS_OPENAPI_PROD + "/uapi/overseas-stock/v1/trading/order-rvsecncl"

    def __init__(
        self,
        client: KoreainvestmentClient,
        account: AccountConfig,
    ):
        self._client = client
        self._account = account
        self._token_manager = TokenManager(client)
    
    def buy(
        self,
        stock_code: str,
        quantity: int,
        price: float,
        exchange: ExchangeCode | str = ExchangeCode.NASD,
    ) -> OverseasOrderResponse:
        """
        해외주식 매수

        Args:
            stock_code: 종목코드 (예: AAPL)
            quantity: 주문수량
            price: 주문단가
            exchange: 거래소코드 (기본값: NASD)
        """
        return self._order(
            stock_code=stock_code,
            quantity=quantity,
            price=price,
            tr_id=OverseasTrId.BUY,
            exchange=exchange,
        )
    
    def sell(
        self,
        stock_code: str,
        quantity: int,
        price: float,
        exchange: ExchangeCode | str = ExchangeCode.NASD,
    ) -> OverseasOrderResponse:
        """
        해외주식 매도

        Args:
            stock_code: 종목코드 (예: AAPL)
            quantity: 주문수량
            price: 주문단가
            exchange: 거래소코드 (기본값: NASD)
        """
        return self._order(
            stock_code=stock_code,
            quantity=quantity,
            price=price,
            tr_id=OverseasTrId.SELL,
            exchange=exchange,
        )
    
    def revise(
        self,
        stock_code: str,
        order_no: str,
        quantity: int,
        price: float,
        exchange: ExchangeCode | str = ExchangeCode.NASD,
    ) -> OverseasOrderResponse:
        """
        해외주식 정정

        Args:
            stock_code: 종목코드
            order_no: 원주문번호
            quantity: 정정수량
            price: 정정단가
            exchange: 거래소코드
        """
        params = OverseasRevisionCancelParam.create_revision(
            account_number=self._account.CANO,
            product_code=self._account.ACNT_PRDT_CD,
            stock_code=stock_code,
            order_no=order_no,
            quantity=quantity,
            price=price,
            exchange=exchange,
        )
        return self._revision_cancel(params)

    def cancel(
        self,
        stock_code: str,
        order_no: str,
        quantity: int,
        exchange: ExchangeCode | str = ExchangeCode.NASD,
    ) -> OverseasOrderResponse:
        """
        해외주식 취소

        Args:
            stock_code: 종목코드
            order_no: 원주문번호
            quantity: 취소수량
            exchange: 거래소코드
        """
        params = OverseasRevisionCancelParam.create_cancel(
            account_number=self._account.CANO,
            product_code=self._account.ACNT_PRDT_CD,
            stock_code=stock_code,
            order_no=order_no,
            quantity=quantity,
            exchange=exchange,
        )
        return self._revision_cancel(params)

    def _order(
        self,
        stock_code: str,
        quantity: int,
        price: float,
        tr_id: OverseasTrId,
        exchange: ExchangeCode | str,
    ):
        """
        해외주식 주문[v1_해외주식-001]
        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/overseas-stock/v1/trading/order
        """
        headers = self._build_headers(tr_id=tr_id.value)
        params = OverseasOrderParam.create(
            account_number=self._account.CANO,
            product_code=self._account.ACNT_PRDT_CD,
            stock_code=stock_code,
            quantity=quantity,
            price=price,
            exchange=exchange,
        )
        logger.debug(f"Order Request - URL: {self.ORDER_URL}")
        logger.debug(f"Order Request - Headers: {headers.to_dict()}")
        logger.debug(f"Order Request - Params: {params.to_dict()}")

        response = self._client._post(
            self.ORDER_URL,
            json=params.to_dict(),
            headers=headers.to_dict(),
        )

        if response.status_code != 200:
            self._handle_error(response)

        return OverseasOrderResponse.from_response(response.json())

    def _revision_cancel(
        self,
        params: OverseasRevisionCancelParam,
    ):
        """
        해외주식 정정취소주문[v1_해외주식-003]
        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/overseas-stock/v1/trading/order-rvsecncl
        """
        headers = self._build_headers(tr_id=OverseasTrId.REVISION_CANCEL.value)
        print(f"Revision/Cancel Request - URL: {self.REVISION_CANCEL_URL}")
        print(f"Request Headers: {headers.to_dict()}")
        print(f"Request Params: {params.to_dict()}")

        """
        response = self._client._post(
            self.REVISION_CANCEL_URL,
            json=params.to_dict(),
            headers=headers.to_dict(),
        )
        """
        response = requests.post(
            self.REVISION_CANCEL_URL,
            json=params.to_dict(),
            headers=headers.to_dict(),
        )

        if response.status_code != 200:
            self._handle_error(response)

        return OverseasOrderResponse.from_response(response.json())

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
        
