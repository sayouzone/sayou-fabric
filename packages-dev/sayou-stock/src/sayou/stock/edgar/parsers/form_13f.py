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
SEC EDGAR 13F 파서
"""

import logging
from typing import Optional
from bs4 import BeautifulSoup

from ..client import EDGARClient
from ..models import (
    Filing13FData, 
    Holding13F, 
    FilingMetadata
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Form13FParser:
    """13F 파일링 파서"""
    
    def __init__(self, client: EDGARClient):
        self.client = client
    
    def fetch_filings(self, cik: str, count: int = 10) -> list[FilingMetadata]:
        """13F 파일링 목록 조회"""
        return self.client.fetch_company_filings(cik, "13F-HR", count)
    
    def extract(self, cik: str, filing_url: str, accession_number: str) -> Filing13FData:
        """13F 데이터 추출"""
        html_docs, json_docs = self.client.fetch_filing_documents(cik, filing_url, accession_number)
        result = Filing13FData(filer_cik=cik)
        
        # 파일 찾기
        info_table_file = None
        primary_doc = None
        
        for item in json_docs.get("directory", {}).get("item", []):
            name = item.get("name", "").lower()
            doc_type = item.get("type", "").upper()
            
            if "infotable" in name or doc_type == "INFORMATION TABLE":
                info_table_file = item.get("name")
            elif name.endswith(".xml") and ("13f" in name or "primary" in name):
                primary_doc = item.get("name")
            elif doc_type == "13F-HR" and name.endswith(".xml"):
                primary_doc = item.get("name")
        
        # Primary 문서에서 기본 정보 추출
        if primary_doc:
            self._extract_header(cik, accession_number, primary_doc, result)
        
        # 정보 테이블에서 보유 종목 추출
        if info_table_file:
            self._extract_holdings(cik, accession_number, info_table_file, result)
        else:
            for item in json_docs.get("directory", {}).get("item", []):
                name = item.get("name", "").lower()
                if name.endswith(".xml") and "info" in name:
                    self._extract_holdings(cik, accession_number, item.get("name"), result)
                    break
        
        # 요약 계산
        self._calculate_summary(result)
        
        return result
    
    def _extract_header(
        self, 
        cik: str, 
        accession_number: str, 
        doc_name: str,
        result: Filing13FData
    ):
        """13F 헤더 정보 추출"""
        try:
            content = self.client.fetch_document_content(cik, accession_number, doc_name)
            soup = BeautifulSoup(content, "xml")
            
            filer_name = soup.find(["filingManager", "name"])
            if filer_name:
                result.filer_name = filer_name.get_text(strip=True)
            
            period = soup.find(["reportCalendarOrQuarter", "periodOfReport"])
            if period:
                result.report_period = period.get_text(strip=True)
            
            filing_date = soup.find("signatureDate")
            if filing_date:
                result.filing_date = filing_date.get_text(strip=True)
                
        except Exception as e:
            print(f"13F 헤더 파싱 오류: {e}")
    
    def _extract_holdings(
        self, 
        cik: str, 
        accession_number: str, 
        doc_name: str,
        result: Filing13FData
    ):
        """13F 정보 테이블에서 보유 종목 추출"""
        try:
            content = self.client.fetch_document_content(cik, accession_number, doc_name)
            soup = BeautifulSoup(content, "xml")
            
            entries = soup.find_all(["infoTable", "infotable", "ns1:infoTable"])
            
            for entry in entries:
                holding = self._parse_entry(entry)
                if holding:
                    result.holdings.append(holding)
            
            result.holdings_count = len(result.holdings)
            result.total_value = sum(h.value for h in result.holdings)
            
        except Exception as e:
            print(f"13F 보유 종목 파싱 오류: {e}")
    
    def _parse_entry(self, entry) -> Optional[Holding13F]:
        """개별 13F 엔트리 파싱"""
        try:
            def find_text(names):
                for name in names:
                    elem = entry.find(name)
                    if elem:
                        return elem.get_text(strip=True)
                return ""
            
            issuer_name = find_text(["nameOfIssuer", "issuer", "ns1:nameOfIssuer"])
            title_of_class = find_text(["titleOfClass", "title", "ns1:titleOfClass"])
            cusip_val = find_text(["cusip", "ns1:cusip"])
            
            value_text = find_text(["value", "ns1:value"])
            value_thousands = float(value_text) if value_text else 0.0
            
            # 주식 수
            shares = 0.0
            shares_type = "SH"
            shares_elem = entry.find(["shrsOrPrnAmt", "ns1:shrsOrPrnAmt"])
            
            if shares_elem:
                amt = shares_elem.find(["sshPrnamt", "ns1:sshPrnamt"])
                if amt:
                    shares = float(amt.get_text(strip=True))
                type_elem = shares_elem.find(["sshPrnamtType", "ns1:sshPrnamtType"])
                if type_elem:
                    shares_type = type_elem.get_text(strip=True)
            
            discretion_val = find_text(["investmentDiscretion", "ns1:investmentDiscretion"]) or "SOLE"
            
            # 의결권
            vote_sole = vote_shared = vote_none = 0
            voting = entry.find(["votingAuthority", "ns1:votingAuthority"])
            
            if voting:
                for tag, attr in [("Sole", "sole"), ("Shared", "shared"), ("None", "none")]:
                    elem = voting.find([tag, tag.lower(), f"ns1:{tag}"])
                    if elem:
                        val = int(elem.get_text(strip=True) or 0)
                        if tag == "Sole":
                            vote_sole = val
                        elif tag == "Shared":
                            vote_shared = val
                        else:
                            vote_none = val
            
            put_call_val = find_text(["putCall", "ns1:putCall"]) or None
            
            return Holding13F(
                issuer_name=issuer_name,
                title_of_class=title_of_class,
                cusip=cusip_val,
                value=value_thousands,
                shares_or_principal=shares,
                shares_or_principal_type=shares_type,
                investment_discretion=discretion_val,
                voting_authority_sole=vote_sole,
                voting_authority_shared=vote_shared,
                voting_authority_none=vote_none,
                put_call=put_call_val
            )
            
        except Exception as e:
            print(f"13F 엔트리 파싱 오류: {e}")
            return None
    
    def _calculate_summary(self, result: Filing13FData):
        """13F 요약 통계 계산"""
        if not result.holdings:
            return
        
        sorted_holdings = sorted(
            result.holdings, 
            key=lambda x: x.value, 
            reverse=True
        )
        
        result.top_holdings = [
            {
                "issuer": h.issuer_name,
                "title": h.title_of_class,
                "cusip": h.cusip,
                "value_thousands": h.value,
                "value_millions": h.value / 1000,
                "shares": h.shares_or_principal,
                "percentage": (h.value / result.total_value * 100) 
                              if result.total_value > 0 else 0
            }
            for h in sorted_holdings[:10]
        ]
    
    def compare(
        self, 
        cik: str, 
        filing_url_current: str,
        filing_url_previous: str,
        accession_current: str, 
        accession_previous: str
    ) -> dict:
        """두 분기의 13F 파일링 비교"""
        current = self.extract(cik, filing_url_current, accession_current)
        previous = self.extract(cik, filing_url_previous, accession_previous)
        
        current_map = {h.cusip: h for h in current.holdings}
        previous_map = {h.cusip: h for h in previous.holdings}
        
        current_cusips = set(current_map.keys())
        previous_cusips = set(previous_map.keys())
        
        # 새로운 포지션
        new_positions = [
            {
                "issuer": current_map[cusip].issuer_name,
                "cusip": cusip,
                "value_thousands": current_map[cusip].value,
                "shares": current_map[cusip].shares_or_principal
            }
            for cusip in (current_cusips - previous_cusips)
        ]
        
        # 청산된 포지션
        closed_positions = [
            {
                "issuer": previous_map[cusip].issuer_name,
                "cusip": cusip,
                "previous_value_thousands": previous_map[cusip].value,
                "previous_shares": previous_map[cusip].shares_or_principal
            }
            for cusip in (previous_cusips - current_cusips)
        ]
        
        # 변동된 포지션
        changed_positions = []
        for cusip in (current_cusips & previous_cusips):
            curr = current_map[cusip]
            prev = previous_map[cusip]
            
            share_change = curr.shares_or_principal - prev.shares_or_principal
            
            if share_change != 0:
                changed_positions.append({
                    "issuer": curr.issuer_name,
                    "cusip": cusip,
                    "current_shares": curr.shares_or_principal,
                    "previous_shares": prev.shares_or_principal,
                    "share_change": share_change,
                    "share_change_pct": (share_change / prev.shares_or_principal * 100) 
                                        if prev.shares_or_principal > 0 else 0,
                    "current_value_thousands": curr.value,
                    "previous_value_thousands": prev.value,
                    "value_change_thousands": curr.value - prev.value,
                })
        
        changed_positions.sort(key=lambda x: abs(x.get("share_change_pct", 0)), reverse=True)
        
        return {
            "current_period": current.report_period,
            "previous_period": previous.report_period,
            "current_total_value": current.total_value,
            "previous_total_value": previous.total_value,
            "total_value_change": current.total_value - previous.total_value,
            "current_holdings_count": current.holdings_count,
            "previous_holdings_count": previous.holdings_count,
            "new_positions": sorted(new_positions, key=lambda x: x["value_thousands"], reverse=True),
            "closed_positions": sorted(closed_positions, key=lambda x: x["previous_value_thousands"], reverse=True),
            "increased_positions": [p for p in changed_positions if p["share_change"] > 0][:20],
            "decreased_positions": [p for p in changed_positions if p["share_change"] < 0][:20],
        }
