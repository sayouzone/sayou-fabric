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
from ..models import (
    RequestHeader,
    BalanceSheetResponse,
    IncomeStatementResponse,
    FinancialRatioResponse,
    ProfitRatioResponse,
    OtherMajorRatioResponse,
    StabilityRatioResponse,
    GrowthRatioResponse,
)
from ..utils.token_manager import TokenManager
from ..utils.utils import (
    KIS_OPENAPI_PROD,
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DomesticFinanceParser:
    """KIS 국내 재무 데이터를 파싱하는 클래스"""

    def __init__(
        self,
        client: KoreainvestmentClient,
    ):
        self._client = client

        self._token_manager = TokenManager(client)

    def balance_sheet(self, stock_code: str, stock_type: str = "300") -> dict:
        """
        국내주식 대차대조표[v1_국내주식-078]
        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/finance/balance-sheet
        """
        url = KIS_OPENAPI_PROD + "/uapi/domestic-stock/v1/finance/balance-sheet"

        headers = self._build_headers(tr_id="CTPF1002R")
        params = {
            "FID_DIV_CLS_CODE": "0",
            "PDNO": stock_code,
            "PRDT_TYPE_CD": stock_type,
        }

        response = self._client._get(url, params=params, headers=headers.to_dict())

        if response.status_code != 200:
            self._handle_error(response)

        return BalanceSheetResponse.from_response(response.json())

    def income_statement(self, stock_code: str) -> dict:
        """
        국내주식 손익계산서[v1_국내주식-079]
        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/finance/income-statement
        """
        url = KIS_OPENAPI_PROD + "/uapi/domestic-stock/v1/finance/income-statement"

        headers = self._build_headers(tr_id="FHKST66430200")
        params = {
            "FID_DIV_CLS_CODE": "0",
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": stock_code,
        }

        response = self._client._get(url, params=params, headers=headers.to_dict())

        if response.status_code != 200:
            self._handle_error(response)

        return IncomeStatementResponse.from_response(response.json())

    def financial_ratio(self, stock_code: str) -> dict:
        """
        국내주식 재무비율[v1_국내주식-080]
        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/finance/financial-ratio
        """
        url = KIS_OPENAPI_PROD + "/uapi/domestic-stock/v1/finance/financial-ratio"

        headers = self._build_headers(tr_id="FHKST66430300")
        params = {
            "FID_DIV_CLS_CODE": "0",
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": stock_code,
        }

        response = self._client._get(url, params=params, headers=headers.to_dict())

        if response.status_code != 200:
            self._handle_error(response)

        return FinancialRatioResponse.from_response(response.json())

    def profit_ratio(self, stock_code: str) -> dict:
        """
        국내주식 수익성비율[v1_국내주식-081]
        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/finance/profit-ratio
        """
        url = KIS_OPENAPI_PROD + "/uapi/domestic-stock/v1/finance/profit-ratio"

        headers = self._build_headers(tr_id="FHKST66430400")
        params = {
            "FID_DIV_CLS_CODE": "0",
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": stock_code,
        }

        response = self._client._get(url, params=params, headers=headers.to_dict())

        if response.status_code != 200:
            self._handle_error(response)

        return ProfitRatioResponse.from_response(response.json())

    def other_major_ratios(self, stock_code: str) -> dict:
        """
        국내주식 기타주요비율[v1_국내주식-082]
        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/finance/other-major-ratios
        """
        url = KIS_OPENAPI_PROD + "/uapi/domestic-stock/v1/finance/other-major-ratios"

        headers = self._build_headers(tr_id="FHKST66430500")
        params = {
            "fid_div_cls_code": "0",
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": stock_code,
        }

        response = self._client._get(url, params=params, headers=headers.to_dict())

        if response.status_code != 200:
            self._handle_error(response)

        return OtherMajorRatioResponse.from_response(response.json())

    def stability_ratio(self, stock_code: str) -> dict:
        """
        국내주식 안정성비율[v1_국내주식-083]
        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/finance/stability-ratio
        """
        url = KIS_OPENAPI_PROD + "/uapi/domestic-stock/v1/finance/stability-ratio"

        headers = self._build_headers(tr_id="FHKST66430600")
        params = {
            "fid_div_cls_code": "0",
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": stock_code,
        }

        response = self._client._get(url, params=params, headers=headers.to_dict())

        if response.status_code != 200:
            self._handle_error(response)

        return StabilityRatioResponse.from_response(response.json())

    def growth_ratio(self, stock_code: str) -> dict:
        """
        국내주식 성장성비율[v1_국내주식-085]
        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/finance/growth-ratio
        """
        url = KIS_OPENAPI_PROD + "/uapi/domestic-stock/v1/finance/growth-ratio"

        headers = self._build_headers(tr_id="FHKST66430800")
        params = {
            "fid_div_cls_code": "0",
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": stock_code,
        }

        response = self._client._get(url, params=params, headers=headers.to_dict())

        if response.status_code != 200:
            self._handle_error(response)

        return GrowthRatioResponse.from_response(response.json())

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
        
