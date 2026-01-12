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

        # Parser initialization
        self._domestic_parser = DomesticParser(self.client)
        self._domestic_finance_parser = DomesticFinanceParser(self.client)
        self._domestic_ksdinfo_parser = DomesticKsdinfoParser(self.client)
        self._overseas_parser = OverseasParser(self.client)
        self._overseas_trading_parser = OverseasTradingParser(self.client)

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

    def overseas_inquire_balance(self):
        return self._overseas_parser.inquire_balance()

    def overseas_buy_stock(self, stock_code: str, order_quantity: int, order_price: float, exchange_type: str = "NASD"):
        return self._overseas_trading_parser.buy_stock(stock_code, order_quantity, order_price, exchange_type)

    def overseas_sell_stock(self, stock_code: str, order_quantity: int, order_price: float, exchange_type: str = "NASD"):
        return self._overseas_trading_parser.sell_stock(stock_code, order_quantity, order_price, exchange_type)