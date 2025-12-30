
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
 
NEWS_BASE_URL = "https://news.naver.com"

NEWS_URLS = {
    '정치': f'{NEWS_BASE_URL}/section/100',
    '경제': f'{NEWS_BASE_URL}/section/101',
    '사회': f'{NEWS_BASE_URL}/section/102',
    '생활/문화': f'{NEWS_BASE_URL}/section/103',
    'IT/과학': f'{NEWS_BASE_URL}/section/105',
    '세계': f'{NEWS_BASE_URL}/section/104',
    'openapi': 'https://openapi.naver.com/v1/search/news.json'
}

FINANCE_URL = 'https://finance.naver.com'
FINANCE_API_URL = 'https://api.finance.naver.com'
MOBILE_URL = 'https://m.stock.naver.com/api/stock'

SISE_COLUMNS = {
    '날짜': 'date',
    '시가': 'open',
    '고가': 'high',
    '저가': 'low',
    '종가': 'close',
    '거래량': 'volume'
}

NEWS_SELECTORS = [
    'a.sa_text_lede',
    'a.sa_text_strong',
    '.sa_text a',
    '.cluster_text_headline a',
    '.cluster_text_lede a'
]

# 뉴스 제목
NEWS_TITLE_SELECTORS = [
    '#title_area span',
    '#ct .media_end_head_headline',
    '.media_end_head_headline',
    'h2#title_area',
    '.news_end_title'
]

# 뉴스 본문
NEWS_CONTENT_SELECTORS = [
    '#dic_area',
    'article#dic_area',
    '.go_trans._article_content',
    '._article_body_contents'
]

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