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

from ..models import AccessToken
from .utils import KIS_OPENAPI_PROD

from ..client import KoreainvestmentClient
from .storage import FileStorage

logger = logging.getLogger(__name__)


class TokenManager:
    """
    액세스 토큰 관리 클래스
    https://apiportal.koreainvestment.com/apiservice-apiservice?/oauth2/tokenP
    """

    OAUTH_URL = KIS_OPENAPI_PROD + "/oauth2/tokenP"

    def __init__(self, client: KoreainvestmentClient):
        self._client = client
        self._token: AccessToken | None = None
        self._storage = FileStorage()

    @property
    def token(self) -> AccessToken:
        """유효한 토큰 반환 (만료 시 자동 갱신)"""
        if self._token is None:
            token = self._storage.read_token()
            self._token = token
        
        if self._token is None or self._token.is_expired:
            self._refresh_token()
        
        return self._token

    @property
    def authorization(self) -> str:
        """Authorization 헤더 값 반환"""
        auth = self.token.authorization
        return auth

    def _refresh_token(self) -> None:
        """토큰 갱신"""
        logger.info("Refreshing access token...")

        params = {
            "appkey": self._client.app_key,
            "appsecret": self._client.app_secret,
            "grant_type": "client_credentials",
        }

        print(self.OAUTH_URL, params)
        response = self._client.post(self.OAUTH_URL, json=params)

        if response.status_code != 200:
            raise Exception(f"Failed to get access token: {response.content}")

        self._token = AccessToken.from_response(response.json())
        logger.info(f"Access token refreshed. Expires at: {self._token.expired_at}")

        self._storage.save_token(self._token)

    def invalidate(self) -> None:
        """토큰 무효화 (강제 갱신 필요 시)"""
        self._token = None