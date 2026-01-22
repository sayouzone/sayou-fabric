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
 
"""
Naver 클라이언트
"""

import logging
import requests
import sys
import time
from pathlib import Path

from .utils import (
    NEWS_URLS,
    FINANCE_URL,
    FINANCE_API_URL
)

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from base.client import BaseClient

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

"""
class NaverClient:
    #Naver 클라이언트
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;'
                      'q=0.9,image/avif,image/webp,image/apng,*/*;' 
                      'q=0.8,application/signed-exchange;v=b3;q=0.7'
        })
        self._rate_limit_delay = 0.1  # FnGuide 요청 제한 준수
    
    def _rate_limit(self):
        #호출 제한
        time.sleep(self._rate_limit_delay)

    def get(self, url: str, params: dict = None, headers: dict = None, referer: str = None, timeout: int = 30) -> requests.Response:
        #GET 요청 (rate limit 적용)
        self._rate_limit()
        
        if referer:
            self.session.headers.update({'Referer': referer})
        
        response = self.session.get(url, params=params, headers=headers, timeout=timeout)

        response.raise_for_status()
        response.encoding = 'utf-8'

        return response
"""

class NaverClient(BaseClient):
    """Korea Investment Securities API Client.
    
    HTTP 클라이언트로서 rate limiting과 자동 재시도 기능을 제공합니다.
    """

    DEFAULT_TIMEOUT: int = 10
    DEFAULT_RATE_LIMIT_DELAY: float = 1.0

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        rate_limit_delay: float = DEFAULT_RATE_LIMIT_DELAY,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """Initialize Korea Investment Client.
        
        Args:
            app_key: API 앱 키
            app_secret: API 앱 시크릿
            rate_limit_delay: 요청 간 대기 시간 (초)
            timeout: 요청 타임아웃 (초)
        """
        super().__init__(rate_limit_delay, timeout)
        self.client_id = client_id
        self.client_secret = client_secret

        if client_id and client_secret:
            news_api_headers = {
                "X-Naver-Client-Id": client_id,
                "X-Naver-Client-Secret": client_secret
            }
            self.session.headers.update(news_api_headers)