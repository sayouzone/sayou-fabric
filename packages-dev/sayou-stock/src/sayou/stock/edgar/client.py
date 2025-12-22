"""
SEC EDGAR API 클라이언트
"""

import time
import json
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from typing import Optional

from .models import FilingMetadata
from .utils import BASE_URL, COMPANY_TICKERS_URL, EDGAR_SEARCH_URL


class EDGARClient:
    """SEC EDGAR API 기본 클라이언트"""
    
    def __init__(self, user_agent: str = "Sayouzone sjkim@sayouzone.com"):
        """
        Args:
            user_agent: SEC에서 요구하는 User-Agent 헤더 (회사명 + 이메일)
        """
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate",
        })
        self._ticker_to_cik: Optional[dict] = None
        self._company_data: Optional[list] = None
        self._rate_limit_delay = 0.1  # SEC 요청 제한 준수
    
    def _rate_limit(self):
        """SEC 요청 제한 준수 (초당 10회 이하)"""
        time.sleep(self._rate_limit_delay)
    
    def _get(self, url: str, params: dict = None) -> requests.Response:
        """GET 요청 (rate limit 적용)"""
        self._rate_limit()
        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        return resp
    
    def fetch_cik_by_ticker(self, ticker: str) -> Optional[str]:
        """티커로 CIK 번호 조회"""
        if self._ticker_to_cik is None:
            resp = self._get(COMPANY_TICKERS_URL)
            data = resp.json()
            #print('Companies:', data)
            self._ticker_to_cik = {
                v["ticker"]: str(v["cik_str"]).zfill(10)
                for v in data.values()
            }
        return self._ticker_to_cik.get(ticker.upper())
    
    def fetch_cik_by_company(self, company: str, limit: int = 10, flags: int = re.IGNORECASE) -> list[dict]:
        """
        정규표현식으로 회사명 검색
        
        Args:
            pattern: 정규표현식 패턴
            limit: 최대 결과 수
            flags: 정규표현식 플래그 (기본: 대소문자 무시)
            
        Returns:
            [{"cik": "0000320193", "ticker": "AAPL", "title": "Apple Inc."}, ...]
            
        Examples:
            # "Apple"로 시작하는 회사
            search_company_by_regex(r"^Apple")
            
            # "Tech" 또는 "Technology" 포함
            search_company_by_regex(r"Tech(nology)?")
            
            # "Inc." 또는 "Corp."로 끝나는 회사
            search_company_by_regex(r"(Inc\.|Corp\.)$")
            
            # 정확히 "Apple Inc." 매칭
            search_company_by_regex(r"^Apple Inc\.$")
        """
        if self._company_data is None:
            resp = self._get(COMPANY_TICKERS_URL)
            data = resp.json()
            #print('Companies:', data)
            self._company_data = list(data.values())

        try:
            regex = re.compile(company, flags)
        except re.error as e:
            print(f"Invalid regex pattern: {e}")
            return []
        
        results = []
        for item in self._company_data:
            title = item.get("title", "")
            if regex.search(title):
                results.append({
                    "cik": str(item["cik_str"]).zfill(10),
                    "ticker": item.get("ticker", ""),
                    "title": title
                })
                if len(results) >= limit:
                    break
        
        return results
    
    def fetch_company_filings(
        self, 
        cik: str, 
        filing_type: str = "10-K", 
        count: int = 10
    ) -> list[FilingMetadata]:
        """
        회사의 파일링 목록 조회
        https://www.sec.gov/cgi-bin/browse-edgar
        """
        cik = cik.zfill(10)
        url = f"{BASE_URL}/cgi-bin/browse-edgar"
        params = {
            "action": "getcompany",
            "CIK": cik,
            "type": filing_type,
            "dateb": "",
            "owner": "include",
            "count": count,
            "output": "atom",
        }
        
        print("Fetching filings:", url, params)
        resp = self._get(url, params)
        soup = BeautifulSoup(resp.content, "xml")
        filings = []
        
        for entry in soup.find_all("entry"):
            accession = entry.find("accession-number")
            if not accession:
                continue
            
            filing_date = entry.find("filing-date")
            filing_href = entry.find("filing-href")
            
            metadata = FilingMetadata(
                accession_number=accession.text.strip(),
                filing_type=filing_type,
                filing_date=filing_date.text.strip() if filing_date else "",
                document_url=filing_href.text.strip() if filing_href else "",
            )
            filings.append(metadata)
        
        return filings

    def fetch_filing_documents(self, cik: str, filing_url: str, accession_number: str):
        """파일링의 문서 목록 조회"""
        cik = cik.zfill(10)
        accession_clean = accession_number.replace("-", "")
        url = f"{BASE_URL}/Archives/edgar/data/{cik}/{accession_clean}/index.json"
        
        print("Filing HTML URL:", filing_url)
        resp_html = self._get(filing_url)
        docs_df = self.extract_document_table(resp_html.text)
        html_docs = json.loads(docs_df.to_json(orient='records'))
        
        print("Filing JSON URL:", url)
        resp_json = self._get(url)
        return html_docs, resp_json.json()

    def extract_document_table(self, html_text: str, summary: str = None) -> pd.DataFrame:
        """
        HTML 테이블에서 href 정보를 포함하여 DataFrame으로 추출
        
        Args:
            html_text: HTML 문자열
            summary: 테이블의 summary 속성값 (선택)
            
        Returns:
            DataFrame with href column
        """
        soup = BeautifulSoup(html_text, "html.parser")
        
        # 테이블 찾기
        if summary:
            table = soup.find("table", {"summary": summary})
        else:
            table = soup.find("table")
        
        if not table:
            return pd.DataFrame()
        
        # 헤더 추출
        headers = []
        header_row = table.find("tr")
        if header_row:
            headers = [th.get_text(strip=True) for th in header_row.find_all("th")]
        
        # 데이터 행 추출
        rows = []
        for tr in table.find_all("tr")[1:]:  # 헤더 제외
            cells = tr.find_all("td")
            if not cells:
                continue
            
            row_data = {}
            for i, td in enumerate(cells):
                col_name = headers[i] if i < len(headers) else f"col_{i}"
                
                # 텍스트 추출
                text = td.get_text(strip=True)
                row_data[col_name] = text if text and text != '\xa0' else None
                
                # 링크가 있으면 href 추출
                link = td.find("a")
                if link and link.get("href"):
                    row_data[f"{col_name}_href"] = (BASE_URL + link.get("href")).replace("/ix?doc=", "")
            
            # 빈 행 제외
            if any(v for k, v in row_data.items() if not k.endswith("_href")):
                rows.append(row_data)

        return pd.DataFrame(rows)
    
    def fetch_document_content(
        self, 
        cik: str, 
        accession_number: str, 
        document_name: str
    ) -> str:
        """특정 파일링 문서 내용 가져오기"""
        cik = cik.zfill(10)
        accession_clean = accession_number.replace("-", "")
        if BASE_URL not in document_name:
            document_name = f"{BASE_URL}/Archives/edgar/data/{cik}/{accession_clean}/{document_name}"
        
        print("Document URL:", document_name)
        resp = self._get(document_name)
        return resp.text
    
    def search_filings(
        self,
        query: str,
        filing_types: list[str] = None,
        start_date: str = None,
        end_date: str = None,
        size: int = 10
    ) -> list[dict]:
        """EDGAR 전문 검색"""
        params = {
            "q": query,
            "dateRange": "custom",
            "startdt": start_date or "2020-01-01",
            "enddt": end_date or "2025-12-31",
            "forms": ",".join(filing_types) if filing_types else "10-K,10-Q,8-K",
            "from": 0,
            "size": size,
        }
        
        resp = self._get(EDGAR_SEARCH_URL, params)
        results = []
        data = resp.json()
        
        for hit in data.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            results.append({
                "cik": source.get("ciks", [""])[0],
                "company_name": source.get("display_names", [""])[0],
                "filing_type": source.get("form", ""),
                "filing_date": source.get("file_date", ""),
                "accession_number": source.get("adsh", ""),
            })
        
        return results
