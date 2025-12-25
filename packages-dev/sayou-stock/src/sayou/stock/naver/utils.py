
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
 

NEWS_URLS = {
    '정치': 'https://news.naver.com/section/100',
    '경제': 'https://news.naver.com/section/101',
    '사회': 'https://news.naver.com/section/102',
    '생활/문화': 'https://news.naver.com/section/103',
    'IT/과학': 'https://news.naver.com/section/105',
    '세계': 'https://news.naver.com/section/104',
    'openapi': 'https://openapi.naver.com/v1/search/news.json'
}

FINANCE_URL = 'https://finance.naver.com'
FINANCE_API_URL = 'https://api.finance.naver.com'
MOBILE_URL = 'https://m.stock.naver.com/api/stock'

def decode_euc_kr(response):
    """깨진 한글 인코딩 복원"""
    
    # 인코딩 변환 (EUC-KR Bytes -> Python Unicode String)
    # response.text를 바로 쓰지 않고, content(바이트)를 직접 디코딩하는 것이 안전합니다.
    try:
        content = response.content.decode('euc-kr')
        return content
    except UnicodeDecodeError:
        # euc-kr로 안 될 경우 cp949 시도 (확장 완성형)
        content = response.content.decode('cp949', errors='replace')
    
    return content