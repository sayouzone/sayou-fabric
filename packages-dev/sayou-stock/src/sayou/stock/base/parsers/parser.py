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
import requests

from ..client import BaseClient
from ..models import BaseRequestHeader, BaseResponseBody

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseParser:
    """Base 파싱 클래스"""

    def __init__(self, client: BaseClient):
        self._client = client

    def fetch(self, url: str, params: dict = None, headers: dict = None):
        """API 호출"""
        response = self._client.get(url, params=params, headers=headers)
        
        if response.status_code != 200:
            self._handle_error(response)
        
        return BaseResponseBody.from_response(response.json())
    
    def _build_headers(self, **kwargs) -> BaseRequestHeader:
        """공통 헤더 생성"""
        return BaseRequestHeader(
            **kwargs
        )

    def _handle_error(self, response) -> None:
        """에러 응답 처리"""
        try:
            error_data = response.json()
            logger.error(f"API Error: {response.status_code} - {response.content}")
            raise Exception(f"API Error: {response.status_code}")
        except ValueError:
            logger.error(f"HTTP Error: {response.status_code} - {response.content}")
            raise Exception(f"HTTP Error: {response.status_code}")