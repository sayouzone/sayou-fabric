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

"""Korea Investment Securities API Client."""

import logging
import sys
from pathlib import Path

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from base.client import BaseClient

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KoreainvestmentClient(BaseClient):
    """Korea Investment Securities API Client.
    
    HTTP 클라이언트로서 rate limiting과 자동 재시도 기능을 제공합니다.
    """

    DEFAULT_TIMEOUT: int = 10
    DEFAULT_RATE_LIMIT_DELAY: float = 1.0

    def __init__(
        self,
        app_key: str | None = None,
        app_secret: str | None = None,
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
        self.app_key = app_key
        self.app_secret = app_secret
