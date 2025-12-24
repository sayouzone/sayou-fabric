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
import requests

from ..client import FnGuideClient

from ..utils import (
    FNGUIDE_URLS
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FnGuideFinanceRatioParser:
    """
    FnGuide 재무비율 파싱 클래스
    
    Snapshot, https://comp.fnguide.com/SVO2/ASP/SVD_FinanceRatio.asp?gicode=A{stock}
    """

    def __init__(self, client: FnGuideClient):
        self.client = client
    
    def parse(self, stock: str):
        """
        기업 정보 | 재무비율 정보 추출 후 주요 키를 영어로 변환
        requests로 HTML을 가져온 후 pandas.read_html()로 파싱

        Args:
            html_text (str): HTML text
            stock: 종목 코드 (회사명을 "company"로 치환하기 위해 사용)

        Returns:
            Dict: 컬럼명이 번역된 DataFrame
        """

        url = FNGUIDE_URLS.get("재무비율")

        if not url:
            return
        
        params = {
            "gicode": f"A{stock}"
        }

        try:
            response = self.client._get(url, params=params)
        except requests.RequestException as e:
            logger.error(f"페이지 요청 실패: {e}")
            return None

        frames = pd.read_html(StringIO(response.text))

        return None