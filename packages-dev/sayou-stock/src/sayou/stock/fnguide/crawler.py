
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
 
from .client import FnGuideClient
#from .models import DartConfig

from .parsers import (
    FnGuideCompanyParser,
    FnGuideComparisonParser,
    FnGuideConsensusParser,
    FnGuideDartParser,
    FnGuideDisclosureParser,
    FnGuideFinanceRatioParser,
    FnGuideFinanceParser,
    FnGuideIndustryAnalysisParser,
    FnGuideInvestParser,
    FnGuideMainParser,
    FnGuideShareAnalysisParser,
)

class FnGuideCrawler:
        
    """DART 공시 문서 크롤러.
    
    기업의 공시 문서를 DART에서 크롤링하여 GCS에 업로드합니다.
    """
    
    # 제외할 공시 유형
    EXCLUDED_REPORT_TYPES = frozenset({"기업설명회(IR)개최(안내공시)"})
    request_delay_seconds = 3

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/120.0.0.0 Safari/537.36'
    }
    
    def __init__(self):
        """크롤러를 초기화합니다.
        
        Args:
            code: 기업 코드 (기본값: 삼성전자)
        """
        self.client = FnGuideClient()

        # 파서 초기화
        self._company_parser = FnGuideCompanyParser(self.client)
        self._comparison_viewer = FnGuideComparisonParser(self.client)
        self._consensus_parser = FnGuideConsensusParser(self.client)
        self._dart_parser = FnGuideDartParser(self.client)
        self._disclosure_parser = FnGuideDisclosureParser(self.client)
        self._finance_ratio_parser = FnGuideFinanceRatioParser(self.client)
        self._finance_parser = FnGuideFinanceParser(self.client)
        self._invest_parser = FnGuideInvestParser(self.client)
        self._industry_parser = FnGuideIndustryAnalysisParser(self.client)
        self._main_parser = FnGuideMainParser(self.client)
        self._share_analysis_parser = FnGuideShareAnalysisParser(self.client)
        self._corp_data : Optional[list] = None

    def main(self, stock: str):
        return self._main_parser.parse(stock)

    def company(self, stock: str):
        return self._company_parser.parse(stock)

    def finance(self, stock: str):
        return self._finance_parser.parse(stock)

    def finance_ratio(self, stock: str):
        return self._finance_ratio_parser.parse(stock)

    def income_statement(self, stock: str):
        return self._finance_parser.income_statement(stock)

    def quarterly_income_statement(self, stock: str):
        return self._finance_parser.quarterly_income_statement(stock)

    def balance_sheet(self, stock: str):
        return self._finance_parser.balance_sheet(stock)

    def quarterly_balance_sheet(self, stock: str):
        return self._finance_parser.quarterly_balance_sheet(stock)

    def cash_flow(self, stock: str):
        return self._finance_parser.cash_flow(stock)

    def quarterly_cash_flow(self, stock: str):
        return self._finance_parser.quarterly_cash_flow(stock)

    def invest(self, stock: str):
        return self._invest_parser.parse(stock)

    def consensus(self, stock: str):
        return self._consensus_parser.parse(stock)

    def share_analysis(self, stock: str):
        return self._share_analysis_parser.parse(stock)

    def industry(self, stock: str):
        return self._industry_parser.parse(stock)

    def comparison(self, stock: str):
        return self._comparison_viewer.parse(stock)

    def disclosure(self, stock: str):
        return self._disclosure_parser.parse(stock)

    def dart(self, stock: str):
        return self._dart_parser.parse(stock)
