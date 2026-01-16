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
    AccountConfig,
    RequestHeader,
    BalanceQueryParam,
    DomesticStockBalance,
    DomesticAccountSummary,
    DomesticBalanceResponse,
    SearchInfoResponse,
    SearchStockInfoResponse,
)
from ..utils.token_manager import TokenManager
from ..utils.utils import (
    KIS_OPENAPI_PROD,
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DomesticParser:
    """KIS 국내 데이터를 파싱하는 클래스"""

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

    def inquire_balance(self) -> dict:
        """
        주식잔고조회
        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/trading/inquire-balance
        """
        url = KIS_OPENAPI_PROD + "/uapi/domestic-stock/v1/trading/inquire-balance"

        headers = self._build_headers(tr_id="TTTC8434R")
        params = BalanceQueryParam(
            CANO=self._account.CANO,
            ACNT_PRDT_CD=self._account.ACNT_PRDT_CD,
            AFHR_FLPR_YN="N",
            INQR_DVSN="01",
            UNPR_DVSN="01",
            FUND_STTL_ICLD_YN="N",
            FNCG_AMT_AUTO_RDPT_YN="N",
            PRCS_DVSN="01",
            CTX_AREA_FK100="",
            CTX_AREA_NK100="",
            OFL_YN="",
        )

        response = self._client.get(
            url,
            params=params.to_dict(),
            headers=headers.to_dict(),
        )

        if response.status_code != 200:
            self._handle_error(response)

        return DomesticBalanceResponse.from_response(response.json())

    def search_info(self, stock_code: str, stock_type: str = "300") -> dict:
        """
        상품기본조회[v1_국내주식-029]
        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/quotations/search-info
        """
        url = KIS_OPENAPI_PROD + "/uapi/domestic-stock/v1/quotations/search-info"

        headers = self._build_headers(tr_id="CTPF1604R")
        params = {
            "PDNO": stock_code,
            "PRDT_TYPE_CD": stock_type,
        }

        response = self._client.get(url, params=params, headers=headers.to_dict())

        if response.status_code != 200:
            self._handle_error(response)

        return SearchInfoResponse.from_response(response.json())

    def search_stock_info(self, stock_code: str, stock_type: str = "300") -> dict:
        """
        주식기본조회[v1_국내주식-067]
        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/quotations/search-stock-info
        """
        url = KIS_OPENAPI_PROD + "/uapi/domestic-stock/v1/quotations/search-stock-info"

        headers = self._build_headers(tr_id="CTPF1002R")
        params = {
            "PDNO": stock_code,
            "PRDT_TYPE_CD": stock_type,
        }

        response = self._client.get(url, params=params, headers=headers.to_dict())

        if response.status_code != 200:
            self._handle_error(response)

        return SearchStockInfoResponse.from_response(response.json())

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
        
