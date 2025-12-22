"""
SEC EDGAR 10-K / 10-Q 파서
"""

import pandas as pd
import re
import json
from typing import Optional
from bs4 import BeautifulSoup
from io import StringIO

from ..client import EDGARClient
from ..models import FinancialData, FilingMetadata
from ..utils import (
    SECTION_PATTERNS_10K, 
    SECTION_PATTERNS_10Q,
    extract_sections,
    find_main_document,
)


class Form10KParser:
    """10-K 파일링 파서"""
    
    def __init__(self, client: EDGARClient):
        self.client = client
    
    def fetch_filings(self, cik: str, count: int = 10) -> list[FilingMetadata]:
        """10-K 파일링 목록 조회"""
        return self.client.fetch_company_filings(cik, "10-K", count)
    
    def extract(self, cik: str, filing_url: str, accession_number: str) -> dict:
        """10-K 데이터 추출"""
        html_docs, json_docs = self.client.fetch_filing_documents(cik, filing_url, accession_number)
        #print('html_docs:', html_docs)
        #print('json_docs:', json_docs)      
        
        result = {
            "sections": {},
            "financial_data": None,
            "risk_factors": [],
            "business_description": "",
        }
        
        # 메인 문서 찾기
        main_doc = find_main_document(html_docs, json_docs, ["10-k"], "10-K")
        print('main_doc', main_doc)
        
        if main_doc:
            content = self.client.fetch_document_content(cik, accession_number, main_doc)

            soup = BeautifulSoup(content, "html.parser")
        
            # 스크립트/스타일 제거
            for tag in soup(["script", "style"]):
                tag.decompose()
            
            text = soup.get_text(separator="\n")
            #print(text)
            
            # 섹션 추출
            result["sections"] = extract_sections(text, SECTION_PATTERNS_10K)
            
            # Risk Factors 추출
            if "Item 1A" in result["sections"]:
                result["risk_factors"] = self._parse_risk_factors(
                    result["sections"]["Item 1A"]
                )
            
            # Business Description 추출
            if "Item 1" in result["sections"]:
                result["business_description"] = result["sections"]["Item 1"][:5000]
        
        # XBRL 재무 데이터 추출
        result["financial_data"] = self._extract_xbrl_financials(cik, accession_number, json_docs)
        
        return result
    
    def _parse_risk_factors(self, risk_section: str) -> list[str]:
        """Risk Factors 섹션에서 개별 리스크 추출"""
        risks = []
        lines = risk_section.split("\n")
        current_risk = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 새로운 리스크 항목 시작 감지
            is_new_risk = (
                (line.isupper() and len(line) > 20) or
                (line.endswith(".") and len(line) < 200 and line[0].isupper())
            )
            
            if is_new_risk:
                if current_risk:
                    risks.append(" ".join(current_risk))
                current_risk = [line]
            else:
                current_risk.append(line)
        
        if current_risk:
            risks.append(" ".join(current_risk))
        
        return risks[:20]
    
    def _extract_xbrl_financials(
        self, 
        cik: str, 
        accession_number: str, 
        docs: dict
    ) -> Optional[FinancialData]:
        """XBRL 파일에서 재무 데이터 추출"""
        
        # XBRL JSON 파일 찾기
        xbrl_json = None
        for item in docs.get("directory", {}).get("item", []):
            name = item.get("name", "")
            if "Financial" in name and name.endswith(".json"):
                xbrl_json = name
                break
        
        if not xbrl_json:
            return None
        
        try:
            content = self.client.fetch_document_content(cik, accession_number, xbrl_json)
            data = json.loads(content)
            
            facts = data.get("facts", {})
            us_gaap = facts.get("us-gaap", {})
            
            financial = FinancialData()
            
            # 매핑 정의
            mappings = {
                "revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", 
                           "SalesRevenueNet", "RevenueFromContractWithCustomerIncludingAssessedTax"],
                "net_income": ["NetIncomeLoss", "ProfitLoss", 
                              "NetIncomeLossAvailableToCommonStockholdersBasic"],
                "total_assets": ["Assets"],
                "total_liabilities": ["Liabilities", "LiabilitiesAndStockholdersEquity"],
                "stockholders_equity": ["StockholdersEquity", 
                                        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
                "eps_basic": ["EarningsPerShareBasic"],
                "eps_diluted": ["EarningsPerShareDiluted"],
                "cash_and_equivalents": ["CashAndCashEquivalentsAtCarryingValue", "Cash"],
            }
            
            for attr, keys in mappings.items():
                value = self._fetch_latest_value(us_gaap, keys)
                if value is not None:
                    setattr(financial, attr, value)
            
            return financial
            
        except Exception as e:
            print(f"XBRL 파싱 오류: {e}")
            return None
    
    def _fetch_latest_value(self, us_gaap: dict, keys: list) -> Optional[float]:
        """US-GAAP 데이터에서 최신 값 추출"""
        for key in keys:
            if key not in us_gaap:
                continue
            
            units = us_gaap[key].get("units", {})
            
            # USD 값
            for unit_type in ["USD", "USD/shares"]:
                values = units.get(unit_type, [])
                if values:
                    sorted_values = sorted(
                        values, 
                        key=lambda x: x.get("end", ""), 
                        reverse=True
                    )
                    if sorted_values:
                        return sorted_values[0].get("val")
        
        return None


class Form10QParser:
    """10-Q 파일링 파서"""
    
    def __init__(self, client: EDGARClient):
        self.client = client
        self._10k_parser = Form10KParser(client)
    
    def fetch_filings(self, cik: str, count: int = 10) -> list[FilingMetadata]:
        """10-Q 파일링 목록 조회"""
        return self.client.fetch_company_filings(cik, "10-Q", count)
    
    def extract(self, cik: str, filing_url: str, accession_number: str) -> dict:
        """10-Q 데이터 추출"""
        html_docs, json_docs = self.client.fetch_filing_documents(cik, filing_url, accession_number)
        
        result = {
            "sections": {},
            "financial_data": None,
            "md_and_a": "",
        }
        
        # 메인 문서 찾기
        main_doc = find_main_document(html_docs, json_docs, ["10-q"], "10-Q")
        
        if main_doc:
            content = self.client.fetch_document_content(cik, accession_number, main_doc)

            soup = BeautifulSoup(content, "html.parser")
        
            # 스크립트/스타일 제거
            for tag in soup(["script", "style"]):
                tag.decompose()
            
            text = soup.get_text(separator="\n")
            
            # 섹션 추출
            result["sections"] = extract_sections(text, SECTION_PATTERNS_10Q)
            
            # MD&A 추출
            if "Item 2" in result["sections"]:
                result["md_and_a"] = result["sections"]["Item 2"][:5000]
        
        # 재무 데이터 (10-K 파서 재사용)
        result["financial_data"] = self._10k_parser._extract_xbrl_financials(
            cik, accession_number, json_docs
        )
        
        return result
