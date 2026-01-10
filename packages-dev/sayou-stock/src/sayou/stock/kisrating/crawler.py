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

from .client import KisratingClient

from .parsers import (
    StatisticsParser,
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KisratingCrawler:
        
    """한국신용평가 > 신용등급 > 등급통계 > 등급별금리스프레드"""
    
    def __init__(self, client_id: str = None, client_secret: str = None):
        """크롤러를 초기화합니다."""
        self.client = KisratingClient()

        # 파서 초기화
        self._statistics_parser = StatisticsParser(self.client)

    def statistics(self, start_date: str = None):
        return self._statistics_parser.fetch(start_date)

    def statistics_excel(self, start_date: str = None):
        return self._statistics_parser.fetch_and_save_excel(start_date)
