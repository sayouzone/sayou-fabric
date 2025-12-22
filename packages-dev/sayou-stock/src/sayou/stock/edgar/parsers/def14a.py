"""
SEC EDGAR DEF 14A (Proxy Statement) 파서
"""

import re
from typing import Optional
from bs4 import BeautifulSoup

from ..client import EDGARClient
from ..models import (
    DEF14AData, 
    ExecutiveCompensation, 
    DirectorInfo,
    ShareholderProposal, 
    OwnershipInfo,
    FilingMetadata,
)
from ..utils import (
    GOVERNANCE_PATTERNS,
    parse_currency,
    parse_int,
    find_main_document,
    is_institution,
)


class DEF14AParser:
    """DEF 14A Proxy Statement 파서"""
    
    def __init__(self, client: EDGARClient):
        self.client = client
    
    def fetch_filings(self, cik: str, count: int = 10) -> list[FilingMetadata]:
        """DEF 14A 파일링 목록 조회"""
        return self.client.fetch_company_filings(cik, "DEF 14A", count)
    
    def extract(self, cik: str, filing_url: str, accession_number: str) -> DEF14AData:
        """DEF 14A 데이터 추출"""
        html_docs, json_docs = self.client.fetch_filing_documents(cik, filing_url, accession_number)
        result = DEF14AData(cik=cik)
        
        main_doc = find_main_document(html_docs, json_docs, ["def14a", "proxy"], "DEF 14A")
        
        if main_doc:
            content = self.client.fetch_document_content(cik, accession_number, main_doc)

            soup = BeautifulSoup(content, "html.parser")
        
            # 스크립트/스타일 제거
            for tag in soup(["script", "style"]):
                tag.decompose()

            text = soup.get_text(separator="\n")
            
            self._extract_meeting_info(text, result)
            self._extract_executive_compensation(soup, text, result)
            self._extract_director_info(soup, text, result)
            self._extract_proposals(text, result)
            self._extract_ownership_info(soup, text, result)
            self._extract_ceo_pay_ratio(text, result)
            self._extract_governance_info(text, result)
        
        return result
    
    def _extract_meeting_info(self, text: str, result: DEF14AData):
        """주주총회 기본 정보 추출"""
        meeting_patterns = [
            r"(?:annual|special)\s+meeting.*?(?:will be held|to be held|held)\s+(?:on\s+)?([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})",
            r"meeting\s+date[:\s]+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})",
        ]
        
        for pattern in meeting_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result.meeting_date = match.group(1).strip()
                break
        
        if re.search(r"annual\s+meeting", text, re.IGNORECASE):
            result.meeting_type = "Annual"
        elif re.search(r"special\s+meeting", text, re.IGNORECASE):
            result.meeting_type = "Special"
        
        record_match = re.search(
            r"record\s+date[:\s]+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})", 
            text, re.IGNORECASE
        )
        if record_match:
            result.record_date = record_match.group(1).strip()
    
    def _extract_executive_compensation(
        self, 
        soup: BeautifulSoup, 
        text: str, 
        result: DEF14AData
    ):
        """임원 보상 테이블 추출"""
        tables = soup.find_all("table")
        comp_table = None
        
        for table in tables:
            table_text = table.get_text().lower()
            if "summary compensation" in table_text or \
               ("name" in table_text and "salary" in table_text and "total" in table_text):
                comp_table = table
                break
        
        if not comp_table:
            return
        
        rows = comp_table.find_all("tr")
        col_indices = {}
        header_found = False
        
        column_mappings = {
            "name": ["name"],
            "year": ["year"],
            "salary": ["salary"],
            "bonus": ["bonus"],
            "stock_awards": ["stock", "award"],
            "option_awards": ["option"],
            "non_equity": ["non-equity", "incentive"],
            "pension": ["pension", "deferred"],
            "other": ["other"],
            "total": ["total"],
        }
        
        for row in rows:
            cells = row.find_all(["td", "th"])
            cell_texts = [c.get_text(strip=True).lower() for c in cells]
            
            if not header_found:
                if any("name" in t or "salary" in t for t in cell_texts):
                    for i, t in enumerate(cell_texts):
                        for col_name, keywords in column_mappings.items():
                            if all(kw in t for kw in keywords):
                                col_indices[col_name] = i
                                break
                    header_found = True
                    continue
            
            if header_found and len(cells) >= 3:
                exec_comp = self._parse_compensation_row(cells, col_indices)
                if exec_comp and exec_comp.total > 0:
                    result.executive_compensation.append(exec_comp)
        
        # CEO 식별
        self._identify_ceo(result)
    
    def _parse_compensation_row(
        self, 
        cells, 
        col_indices: dict
    ) -> Optional[ExecutiveCompensation]:
        """보상 테이블 행 파싱"""
        try:
            name = cells[col_indices.get("name", 0)].get_text(strip=True)
            
            if not name or name.lower() in ["name", "principal position", ""]:
                return None
            
            exec_comp = ExecutiveCompensation(
                name=name,
                title=self._extract_title(name)
            )
            
            field_mappings = {
                "year": ("year", parse_int),
                "salary": ("salary", parse_currency),
                "bonus": ("bonus", parse_currency),
                "stock_awards": ("stock_awards", parse_currency),
                "option_awards": ("option_awards", parse_currency),
                "non_equity": ("non_equity_incentive", parse_currency),
                "pension": ("pension_change", parse_currency),
                "other": ("other_compensation", parse_currency),
                "total": ("total", parse_currency),
            }
            
            for col_key, (attr, parser) in field_mappings.items():
                if col_key in col_indices:
                    value = parser(cells[col_indices[col_key]].get_text(strip=True))
                    setattr(exec_comp, attr, value)
            
            if exec_comp.total == 0:
                exec_comp.total = exec_comp.calculate_total()
            
            return exec_comp
            
        except Exception:
            return None
    
    def _extract_title(self, name_cell: str) -> str:
        """이름 셀에서 직책 추출"""
        parts = re.split(r'[\n,]', name_cell)
        return parts[1].strip() if len(parts) > 1 else ""
    
    def _identify_ceo(self, result: DEF14AData):
        """CEO 식별"""
        if not result.executive_compensation:
            return
        
        for exec_comp in result.executive_compensation:
            title_lower = exec_comp.title.lower()
            if "ceo" in title_lower or "chief executive" in title_lower:
                result.ceo_name = exec_comp.name
                return
        
        result.ceo_name = result.executive_compensation[0].name
    
    def _extract_director_info(
        self, 
        soup: BeautifulSoup, 
        text: str, 
        result: DEF14AData
    ):
        """이사회 정보 추출"""
        directors = []
        seen_names = set()
        
        # 패턴으로 추출
        director_pattern = r"(?:^|\n)([A-Z][a-z]+(?:\s+[A-Z]\.?\s+)?[A-Z][a-z]+)[,\s]+(?:age\s+)?(\d{2,3})?[,\s]*(?:has been|has served|is|serves as|director)"
        matches = re.findall(director_pattern, text, re.MULTILINE)
        
        for match in matches:
            name = match[0].strip()
            if name in seen_names or len(name) <= 5:
                continue
            
            seen_names.add(name)
            age = int(match[1]) if match[1] else None
            
            director = DirectorInfo(name=name, age=age)
            
            name_context = text[text.find(name):text.find(name) + 500]
            director.independent = bool(re.search(r"independent", name_context, re.IGNORECASE))
            
            directors.append(director)
        
        # 테이블에서도 추출
        self._extract_directors_from_tables(soup, directors, seen_names)
        
        result.directors = directors[:20]
        result.board_size = len(result.directors)
        result.independent_directors = sum(1 for d in result.directors if d.independent)
    
    def _extract_directors_from_tables(
        self, 
        soup: BeautifulSoup, 
        directors: list, 
        seen_names: set
    ):
        """테이블에서 이사 정보 추출"""
        for table in soup.find_all("table"):
            table_text = table.get_text().lower()
            if "director" not in table_text:
                continue
            if "age" not in table_text and "since" not in table_text:
                continue
            
            for row in table.find_all("tr")[1:]:
                cells = row.find_all(["td", "th"])
                if len(cells) < 2:
                    continue
                
                name = cells[0].get_text(strip=True)
                if not name or len(name) <= 3 or name in seen_names:
                    continue
                
                seen_names.add(name)
                director = DirectorInfo(name=name)
                
                for cell in cells[1:]:
                    cell_text = cell.get_text(strip=True)
                    age_match = re.match(r'^(\d{2,3})$', cell_text)
                    if age_match:
                        director.age = int(age_match.group(1))
                        break
                
                directors.append(director)
    
    def _extract_proposals(self, text: str, result: DEF14AData):
        """주주 제안 및 투표 안건 추출"""
        proposals = []
        
        proposal_patterns = [
            r"Proposal\s+(?:No\.?\s*)?(\d+)[:\s]+(.+?)(?=Proposal\s+(?:No\.?\s*)?\d+|$)",
            r"Item\s+(\d+)[:\s]+(.+?)(?=Item\s+\d+|$)",
        ]
        
        for pattern in proposal_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if not matches:
                continue
            
            for num, title in matches:
                title_clean = re.sub(r'\s+', ' ', title.strip())[:200]
                
                if len(title_clean) < 10:
                    continue
                
                proposal = ShareholderProposal(
                    proposal_number=int(num),
                    title=title_clean
                )
                
                # Board Recommendation
                rec_pattern = rf"Proposal\s+(?:No\.?\s*)?{num}.*?(?:board|our)\s+recommend(?:s|ation)[:\s]+(\w+)"
                rec_match = re.search(rec_pattern, text, re.IGNORECASE | re.DOTALL)
                if rec_match:
                    rec = rec_match.group(1).upper()
                    if rec in ["FOR", "AGAINST", "ABSTAIN"]:
                        proposal.board_recommendation = rec
                
                proposals.append(proposal)
            break
        
        # 일반적인 안건 감지
        self._detect_common_proposals(text, proposals)
        result.proposals = proposals
    
    def _detect_common_proposals(self, text: str, proposals: list):
        """일반적인 안건 유형 감지"""
        common_patterns = [
            (r"election\s+of\s+directors", "Election of Directors"),
            (r"ratif(?:y|ication)\s+.*?(?:independent\s+)?auditor", "Ratification of Auditors"),
            (r"advisory\s+(?:vote|approval)\s+.*?(?:executive\s+)?compensation", "Say on Pay"),
            (r"say.?on.?pay", "Say on Pay"),
            (r"approve\s+.*?(?:equity|incentive|stock)\s+plan", "Equity Compensation Plan"),
            (r"amend(?:ment)?\s+.*?(?:certificate|charter|bylaws)", "Charter/Bylaws Amendment"),
        ]
        
        for pattern, title in common_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                if not any(title.lower() in p.title.lower() for p in proposals):
                    proposals.append(ShareholderProposal(
                        proposal_number=len(proposals) + 1,
                        title=title,
                        board_recommendation="FOR"
                    ))
    
    def _extract_ownership_info(
        self, 
        soup: BeautifulSoup, 
        text: str, 
        result: DEF14AData
    ):
        """주요 주주 정보 추출"""
        shareholders = []
        
        for table in soup.find_all("table"):
            table_text = table.get_text().lower()
            if "beneficial" not in table_text or "percent" not in table_text:
                continue
            
            for row in table.find_all("tr")[1:]:
                owner = self._parse_ownership_row(row)
                if owner:
                    shareholders.append(owner)
            break
        
        result.major_shareholders = shareholders[:20]
        result.insider_ownership_pct = sum(
            s.percentage for s in shareholders if s.is_insider
        )
        result.institutional_ownership_pct = sum(
            s.percentage for s in shareholders if s.is_institution
        )
    
    def _parse_ownership_row(self, row) -> Optional[OwnershipInfo]:
        """주주 정보 행 파싱"""
        cells = row.find_all(["td", "th"])
        if len(cells) < 2:
            return None
        
        name = cells[0].get_text(strip=True)
        if not name or len(name) < 3 or re.match(r'^[\d,.\s%]+$', name):
            return None
        
        owner = OwnershipInfo(name=name)
        owner.is_institution = is_institution(name)
        owner.is_insider = not owner.is_institution
        
        for cell in cells[1:]:
            cell_text = cell.get_text(strip=True)
            
            pct_match = re.search(r'([\d.]+)\s*%', cell_text)
            if pct_match and owner.percentage == 0:
                owner.percentage = float(pct_match.group(1))
            
            shares_match = re.match(r'^([\d,]+)$', cell_text.replace(',', ''))
            if shares_match and owner.shares == 0:
                owner.shares = parse_int(cell_text)
        
        return owner if owner.percentage > 0 or owner.shares > 0 else None
    
    def _extract_ceo_pay_ratio(self, text: str, result: DEF14AData):
        """CEO Pay Ratio 추출"""
        ratio_patterns = [
            r"(?:ceo|chief executive).*?pay\s+ratio.*?(\d+)\s*(?:to|:)\s*1",
            r"pay\s+ratio.*?(\d+)\s*(?:to|:)\s*1",
            r"(\d+)\s*(?:to|:)\s*1\s*(?:ratio|pay ratio)",
        ]
        
        for pattern in ratio_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result.ceo_pay_ratio = float(match.group(1))
                break
        
        median_patterns = [
            r"median\s+(?:annual\s+)?(?:total\s+)?compensation.*?\$?([\d,]+)",
            r"median\s+employee.*?\$?([\d,]+)",
        ]
        
        for pattern in median_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result.median_employee_pay = parse_currency(match.group(1))
                break
    
    def _extract_governance_info(self, text: str, result: DEF14AData):
        """거버넌스 정보 추출"""
        governance_items = []
        
        for pattern, description in GOVERNANCE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                governance_items.append(description)
        
        result.governance_highlights = governance_items
        
        # Say on Pay 빈도
        if re.search(r"say.?on.?pay.*?every\s+year|annual.*?say.?on.?pay", text, re.IGNORECASE):
            result.say_on_pay_vote = "Annual"
        elif re.search(r"say.?on.?pay.*?every\s+two\s+years|biennial", text, re.IGNORECASE):
            result.say_on_pay_vote = "Biennial"
        elif re.search(r"say.?on.?pay.*?every\s+three\s+years|triennial", text, re.IGNORECASE):
            result.say_on_pay_vote = "Triennial"
        
        support_match = re.search(
            r"(?:last|prior|previous)\s+year.*?say.?on.?pay.*?(\d+(?:\.\d+)?)\s*%",
            text, re.IGNORECASE
        )
        if support_match:
            result.prior_say_on_pay_support = float(support_match.group(1))
    
    def analyze_compensation_trends(self, cik: str, years: int = 3) -> dict:
        """여러 연도의 임원 보상 트렌드 분석"""
        filings = self.fetch_filings(cik, count=years)
        yearly_data = []
        
        for filing in filings:
            data = self.extract(cik, filing.document_url, filing.accession_number)
            
            if data.executive_compensation:
                ceo_comp = None
                total_comp = sum(e.total for e in data.executive_compensation)
                
                for exec_comp in data.executive_compensation:
                    if exec_comp.name == data.ceo_name:
                        ceo_comp = exec_comp.total
                        break
                
                yearly_data.append({
                    "filing_date": filing.filing_date,
                    "ceo_name": data.ceo_name,
                    "ceo_total_compensation": ceo_comp,
                    "ceo_pay_ratio": data.ceo_pay_ratio,
                    "total_named_exec_compensation": total_comp,
                    "number_of_named_executives": len(data.executive_compensation),
                    "median_employee_pay": data.median_employee_pay,
                })
        
        # YoY 변화율 계산
        for i in range(len(yearly_data) - 1):
            current = yearly_data[i]
            previous = yearly_data[i + 1]
            
            if current.get("ceo_total_compensation") and previous.get("ceo_total_compensation"):
                change = (
                    (current["ceo_total_compensation"] - previous["ceo_total_compensation"]) 
                    / previous["ceo_total_compensation"] * 100
                )
                current["ceo_comp_yoy_change_pct"] = round(change, 2)
        
        return {
            "company_cik": cik,
            "years_analyzed": len(yearly_data),
            "compensation_by_year": yearly_data
        }
    
    def compare_peers(self, ciks: list[str]) -> list[dict]:
        """여러 회사의 임원 보상 비교"""
        comparison = []
        
        for cik in ciks:
            try:
                filings = self.fetch_filings(cik, count=1)
                if not filings:
                    continue
                
                data = self.extract(cik, filings[0].document_url, filings[0].accession_number)
                
                ceo_comp = None
                for exec_comp in data.executive_compensation:
                    if exec_comp.name == data.ceo_name:
                        ceo_comp = exec_comp
                        break
                
                if not ceo_comp and data.executive_compensation:
                    ceo_comp = data.executive_compensation[0]
                
                comparison.append({
                    "cik": cik,
                    "company_name": data.company_name,
                    "ceo_name": data.ceo_name,
                    "ceo_total_compensation": ceo_comp.total if ceo_comp else 0,
                    "ceo_salary": ceo_comp.salary if ceo_comp else 0,
                    "ceo_stock_awards": ceo_comp.stock_awards if ceo_comp else 0,
                    "ceo_pay_ratio": data.ceo_pay_ratio,
                    "board_size": data.board_size,
                    "independent_directors": data.independent_directors,
                    "filing_date": filings[0].filing_date,
                })
                
            except Exception as e:
                print(f"Error processing CIK {cik}: {e}")
        
        comparison.sort(key=lambda x: x.get("ceo_total_compensation", 0), reverse=True)
        return comparison
