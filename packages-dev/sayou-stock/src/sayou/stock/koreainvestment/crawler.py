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

import logging

from .client import KoreainvestmentClient
from .models import AccountConfig
from .parsers import (
    DomesticParser,
    DomesticFinanceParser,
    DomesticKsdinfoParser,
    OverseasParser,
    OverseasTradingParser,
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KoreainvestmentCrawler:
        
    """Koreainvestment Crawler"""
    
    def __init__(self, app_key: str = None, app_secret: str = None):
        """Initialize Koreainvestment Crawler"""
        self.client = KoreainvestmentClient(app_key, app_secret)

        self._account = AccountConfig(
            account_number="72749154",
            product_code="01",
        )

        # Parser initialization
        self._domestic_parser = DomesticParser(self.client)
        self._domestic_finance_parser = DomesticFinanceParser(self.client)
        self._domestic_ksdinfo_parser = DomesticKsdinfoParser(self.client)
        self._overseas_parser = OverseasParser(self.client)
        self._overseas_trading_parser = OverseasTradingParser(self.client, self._account)

    def domestic(self, start_date: str = None):
        return self._domestic_parser.fetch(start_date)

    def inquire_balance(self):
        return self._domestic_parser.inquire_balance()

    def search_info(self, stock_code: str, stock_type: str = "300"):
        return self._domestic_parser.search_info(stock_code, stock_type)

    def search_stock_info(self, stock_code: str, stock_type: str = "300"):
        return self._domestic_parser.search_stock_info(stock_code, stock_type)

    def balance_sheet(self, stock_code: str):
        return self._domestic_finance_parser.balance_sheet(stock_code)

    def income_statement(self, stock_code: str):
        return self._domestic_finance_parser.income_statement(stock_code)

    def financial_ratio(self, stock_code: str):
        return self._domestic_finance_parser.financial_ratio(stock_code)

    def profit_ratio(self, stock_code: str):
        return self._domestic_finance_parser.profit_ratio(stock_code)

    def other_major_ratios(self, stock_code: str):
        return self._domestic_finance_parser.other_major_ratios(stock_code)

    def stability_ratio(self, stock_code: str):
        return self._domestic_finance_parser.stability_ratio(stock_code)

    def growth_ratio(self, stock_code: str):
        return self._domestic_finance_parser.growth_ratio(stock_code)

    def dividend(self, stock_code: str):
        return self._domestic_ksdinfo_parser.dividend(stock_code)

    def inquire_balance_overseas(self):
        return self._overseas_parser.inquire_balance()

    def buy_stock_overseas(self, stock_code: str, order_quantity: int, order_price: float, exchange_type: str):
        return self._overseas_trading_parser.buy(stock_code, order_quantity, order_price, exchange_type)

    def sell_stock_overseas(self, stock_code: str, order_quantity: int, order_price: float, exchange_type: str):
        return self._overseas_trading_parser.sell(stock_code, order_quantity, order_price, exchange_type)

    def revise_stock_overseas(
        self,
        stock_code: str,
        quantity: int,
        price: float,
        order_no: str,
        exchange_type: str,
    ):    
        """해외주식 정정주문"""
        return self._overseas_trading_parser.revise(stock_code, order_no, quantity, price, exchange=exchange_type)

    def cancel_stock_overseas(
        self,
        stock_code: str,
        quantity: int,
        price: float,
        order_no: str,
        exchange_type: str,
    ):
        """해외주식 취소주문"""
        return self._overseas_trading_parser.cancel(stock_code, order_no, quantity, exchange=exchange_type)