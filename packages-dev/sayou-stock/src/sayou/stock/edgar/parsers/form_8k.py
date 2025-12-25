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
SEC EDGAR 8-K 파서
"""

import logging
import re
from typing import Optional
from bs4 import BeautifulSoup

from ..client import EDGARClient
from ..models import (
    Filing8KData, 
    FilingMetadata
)
from ..utils import (
    ITEM_8K_MAPPING, 
    find_main_document
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Form8KParser:
    """8-K 파일링 파서"""
    
    def __init__(self, client: EDGARClient):
        self.client = client
    
    def fetch_filings(self, cik: str, count: int = 10) -> list[FilingMetadata]:
        """8-K 파일링 목록 조회"""
        return self.client.fetch_company_filings(cik, "8-K", count)
    
    def extract(self, cik: str, filing_url: str, accession_number: str) -> Filing8KData:
        """8-K 데이터 추출"""
        html_docs, json_docs = self.client.fetch_filing_documents(cik, filing_url, accession_number)
        result = Filing8KData()
        
        # 메인 문서 찾기
        main_doc = find_main_document(html_docs, json_docs, ["8-k"], "8-K")
        
        if main_doc:
            content = self.client.fetch_document_content(cik, accession_number, main_doc)

            soup = BeautifulSoup(content, "html.parser")
        
            # 스크립트/스타일 제거
            for tag in soup(["script", "style"]):
                tag.decompose()
            
            text = soup.get_text(separator="\n")
            
            # 아이템 추출
            items = self._extract_items(text)
            result.items = items
            
            # 각 아이템 설명
            for item_code in items:
                if item_code in ITEM_8K_MAPPING:
                    result.event_descriptions.append({
                        "item": item_code,
                        "description": ITEM_8K_MAPPING[item_code],
                        "content": self._extract_item_content(text, item_code)
                    })
        
        return result
    
    def _extract_items(self, text: str) -> list[str]:
        """8-K에서 보고된 아이템 번호 추출"""
        items = []
        pattern = r"Item\s*(\d+\.\d+)"
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        for match in matches:
            if match in ITEM_8K_MAPPING and match not in items:
                items.append(match)
        
        return items
    
    def _extract_item_content(self, text: str, item_code: str) -> str:
        """특정 8-K 아이템의 내용 추출"""
        pattern = rf"Item\s*{re.escape(item_code)}[.\s]+"
        match = re.search(pattern, text, re.IGNORECASE)
        
        if not match:
            return ""
        
        start = match.end()
        end_pattern = r"Item\s*\d+\.\d+|SIGNATURE"
        end_match = re.search(end_pattern, text[start:], re.IGNORECASE)
        end = start + end_match.start() if end_match else start + 5000
        
        return text[start:end].strip()[:3000]
