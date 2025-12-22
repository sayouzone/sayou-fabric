"""
Naver 클라이언트
"""

import requests
import time

from .utils import (
    news_urls,
    finance_url
)

class NaverClient:
    """Naver 클라이언트"""
    
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
        """호출 제한"""
        time.sleep(self._rate_limit_delay)

    def _get(self, url: str, params: dict = None, headers: dict = None, referer: str = None, timeout: int = 30) -> requests.Response:
        """GET 요청 (rate limit 적용)"""
        self._rate_limit()
        
        if referer:
            self.session.headers.update({'Referer': referer})
        
        response = self.session.get(url, params=params, headers=headers, timeout=timeout)

        response.raise_for_status()
        response.encoding = 'utf-8'

        return response