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

from __future__ import annotations

import logging
import time

import requests

from typing import Any

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KoreainvestmentClient:
    """Korea Investment Securities API Client.
    
    HTTP 클라이언트로서 rate limiting과 자동 재시도 기능을 제공합니다.
    """

    DEFAULT_HEADERS: dict[str, str] = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/avif,image/webp,image/apng,*/*;"
            "q=0.8,application/signed-exchange;v=b3;q=0.7"
        ),
    }

    DEFAULT_TIMEOUT: int = 10
    DEFAULT_RATE_LIMIT_DELAY: float = 1.0
    
    # Retry 설정
    INITIAL_RETRY_DELAY: float = 1.0
    MAX_RETRY_DELAY: float = 32.0
    RETRY_BACKOFF_MULTIPLIER: int = 2

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
        self.app_key = app_key
        self.app_secret = app_secret
        self._rate_limit_delay = rate_limit_delay
        self._timeout = timeout
        
        self._session = requests.Session()
        self._session.headers.update(self.DEFAULT_HEADERS)
    
    def _rate_limit(self) -> None:
        """Rate limit 적용을 위한 대기."""
        if self._rate_limit_delay > 0:
            time.sleep(self._rate_limit_delay)

    def _build_headers(
        self,
        extra_headers: dict[str, str] | None = None,
        referer: str | None = None,
    ) -> dict[str, str]:
        """요청용 헤더를 구성합니다.
        
        Args:
            extra_headers: 추가 헤더
            referer: Referer 헤더 값
            
        Returns:
            병합된 헤더 딕셔너리
        """
        headers: dict[str, str] = {}
        
        if extra_headers:
            headers.update(extra_headers)
        
        if referer:
            headers["Referer"] = referer
        
        return headers

    def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> requests.Response:
        """재시도 로직이 포함된 HTTP 요청을 수행합니다.
        
        Args:
            method: HTTP 메서드 (GET, POST 등)
            url: 요청 URL
            **kwargs: requests 라이브러리에 전달할 추가 인자
            
        Returns:
            HTTP 응답 객체
            
        Raises:
            requests.exceptions.RequestException: 최대 재시도 횟수 초과 또는 복구 불가능한 에러
        """
        retry_delay = self.INITIAL_RETRY_DELAY
        last_exception: Exception | None = None

        while retry_delay <= self.MAX_RETRY_DELAY:
            try:
                response = self._session.request(method, url, **kwargs)
                response.raise_for_status()
                response.encoding = "utf-8"
                return response
            
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                logger.warning(
                    "Connection error (retrying in %.1fs): %s", 
                    retry_delay, 
                    e,
                )
                time.sleep(retry_delay)
                retry_delay *= self.RETRY_BACKOFF_MULTIPLIER
            
            except requests.exceptions.RequestException:
                raise

        logger.error("Max retries exceeded for %s %s", method, url)
        raise requests.exceptions.ConnectionError(
            f"Max retries exceeded: {last_exception}"
        ) from last_exception

    def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        referer: str | None = None,
        timeout: int | None = None,
    ) -> requests.Response:
        """
        GET Request (Rate Limit)
        
        Args:
            url: 요청 URL
            params: URL 파라미터
            headers: 추가 헤더
            referer: Referer 헤더 값
            timeout: 요청 타임아웃 (초)
        
        Returns:
            HTTP 응답 객체
        """
        self._rate_limit()

        return self._request_with_retry(
            method="GET",
            url=url,
            params=params,
            headers=self._build_headers(headers, referer),
            timeout=timeout or self._timeout,
        )

    def post(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        referer: str | None = None,
        timeout: int | None = None,
    ) -> requests.Response:
        """
        POST Request (Rate Limit)
        
        Args:
            url: 요청 URL
            params: URL 파라미터
            data: POST 데이터
            json: JSON 데이터
            headers: 추가 헤더
            referer: Referer 헤더 값
            timeout: 요청 타임아웃 (초), None이면 기본값 사용
        
        Returns:
            HTTP 응답 객체
        """
        self._rate_limit()

        return self._request_with_retry(
            method="POST",
            url=url,
            params=params,
            data=data,
            json=json,
            headers=self._build_headers(headers, referer),
            timeout=timeout or self._timeout,
        )