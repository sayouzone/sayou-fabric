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

from io import StringIO
from lxml import html
from typing import Optional

from ..client import KisratingClient
from ..models import (
    Statistics,
    XPathConfig,
    FileType,
    DownloadFile
)
from .html_extractor import HtmlTableExtractor
from ..utils.storage import FileStorage
from ..utils.utils import (
    _STATISTICS_SPREAD_URL_,
    _STATISTICS_SPREAD_EXCEL_URL_,
    get_filename,
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StatisticsParser:
    """KIS Rating 통계 데이터를 파싱하는 클래스"""

    DEFAULT_LOCAL_PATH = './statistics'

    def __init__(
        self,
        client: KisratingClient,
        config: Optional[XPathConfig] = None,
        local_path: Optional[str] = None,
    ):
        self.client = client

        self._config = config or XPathConfig()
        self._extractor = HtmlTableExtractor()
        self._storage = FileStorage(local_path or self.DEFAULT_LOCAL_PATH)
    
    def fetch(self, start_date: str) -> Statistics:
        """
        통계 데이터를 조회하여 DataFrame으로 반환합니다.
        
        Args:
            start_date: 조회 시작일 (예: '2024-01-01')
            
        Returns:
            Statistics: 수익률/스프레드 데이터
        """
        # POST 요청에 담을 데이터 (payload)
        payload = {"startDt": start_date}

        response = self.client._post(_STATISTICS_SPREAD_URL_, data=payload)

        yield_df = self._extractor.extract_by_xpath(response.text, self._config.yield_xpath)
        spread_df = self._extractor.extract_by_xpath(response.text, self._config.spread_xpath)

        return Statistics(yield_df=yield_df, spread_df=spread_df)
    
    def fetch_and_save_excel(self, start_date: str) -> DownloadFile:
        """
        통계 데이터를 엑셀 파일로 다운로드하여 저장합니다.
        
        Args:
            start_date: 조회 시작일 (예: '2024-01-01')
            
        Returns:
            DownloadFile: 저장된 파일 정보
        """
        payload = {"startDt": start_date}

        response = self.client._post(_STATISTICS_SPREAD_EXCEL_URL_, data=payload)
        headers = response.headers

        filename = get_filename(headers)
        file_type = FileType.from_filename(filename)
        file_path = self._storage.save(filename, response.content)

        return DownloadFile(
            filename=filename, 
            filepath=file_path, 
            content=response.content, 
            file_type=file_type
        )