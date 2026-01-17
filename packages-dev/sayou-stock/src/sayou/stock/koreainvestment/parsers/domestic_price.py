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
import json
import os
import pandas as pd
import requests
import time

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ..client import KoreainvestmentClient
from ..models import (
    RequestHeader,
    DailyPriceParam,
    StockCurrentPriceResponse,
    StockDailyPriceResponse,
)
from ..utils.token_manager import TokenManager
from ..utils.utils import (
    KIS_OPENAPI_PROD,
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DomesticPriceParser:
    """KIS 국내 주식 가격 데이터를 파싱하는 클래스"""

    PRICE_URL = KIS_OPENAPI_PROD + "/uapi/domestic-stock/v1/quotations/inquire-price"
    DAILY_PRICE_URL = KIS_OPENAPI_PROD + "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"

    def __init__(
        self,
        client: KoreainvestmentClient,
    ):
        self._client = client

        self._token_manager = TokenManager(client)

    def price(
        self,
        stock_code: str,
    ) -> pd.DataFrame:
        """주식현재가 데이터 조회
        주식현재가 시세[v1_국내주식-008]
        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/quotations/inquire-price
        
        Args:
            stock_code: 종목코드 (6자리)
            period: 조회 기간 (일)
            start_date: 조회 시작일 (YYYYMMDD)
            end_date: 조회 종료일 (YYYYMMDD)
            adjust_price: 수정주가 (0:수정주가, 1:원주가)
        
        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        
        params = DailyPriceParam(
            FID_COND_MRKT_DIV_CODE="J",
            FID_INPUT_ISCD=stock_code,
        )
        
        headers = self._build_headers("FHKST01010100")
        logger.info(f"가격 조회 요청: {params.to_dict()}")
        
        response = self._client.get(self.PRICE_URL, headers=headers.to_dict(), params=params.to_dict())
        
        if response.status_code != 200:
            raise Exception(f"가격 조회 실패: {response.text}")
        
        return StockCurrentPriceResponse.from_response(response.json())


    def daily_price(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "D",
        adjust_price: int = 0,
    ) -> pd.DataFrame:
        """일봉 데이터 조회
        국내주식기간별시세(일/주/월/년)[v1_국내주식-016]
        https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice
        
        Args:
            stock_code: 종목코드 (6자리)
            period: 조회 기간 (일)
            start_date: 조회 시작일 (YYYYMMDD)
            end_date: 조회 종료일 (YYYYMMDD)
            adjust_price: 수정주가 (0:수정주가, 1:원주가)
        
        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        
        start_date = start_date or ""
        end_date = end_date or datetime.now().strftime("%Y%m%d")

        params = DailyPriceParam(
            FID_COND_MRKT_DIV_CODE="J",
            FID_INPUT_ISCD=stock_code,
            FID_INPUT_DATE_1=start_date,
            FID_INPUT_DATE_2=end_date,
            FID_PERIOD_DIV_CODE=period,
            FID_ORG_ADJ_PRC=adjust_price,
        )
        
        headers = self._build_headers("FHKST03010100")
        #logger.info(f"일봉 조회 요청: {params.to_dict()}")
        
        response = self._client.get(self.DAILY_PRICE_URL, headers=headers.to_dict(), params=params.to_dict())
        
        if response.status_code != 200:
            raise Exception(f"일봉 조회 실패: {response.text}")
        
        return StockDailyPriceResponse.from_response(response.json())

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
        
