"""
SEC EDGAR 유틸리티 함수 및 상수
"""

import re
from typing import Optional


# ============================================================
# 상수 정의
# ============================================================

BASE_URL = "https://www.sec.gov"
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"

# 8-K 아이템 코드 매핑
ITEM_8K_MAPPING = {
    "1.01": "Entry into a Material Definitive Agreement",
    "1.02": "Termination of a Material Definitive Agreement",
    "1.03": "Bankruptcy or Receivership",
    "1.04": "Mine Safety - Reporting of Shutdowns and Patterns of Violations",
    "2.01": "Completion of Acquisition or Disposition of Assets",
    "2.02": "Results of Operations and Financial Condition",
    "2.03": "Creation of a Direct Financial Obligation",
    "2.04": "Triggering Events That Accelerate or Increase Obligation",
    "2.05": "Costs Associated with Exit or Disposal Activities",
    "2.06": "Material Impairments",
    "3.01": "Notice of Delisting or Transfer",
    "3.02": "Unregistered Sales of Equity Securities",
    "3.03": "Material Modification to Rights of Security Holders",
    "4.01": "Changes in Registrant's Certifying Accountant",
    "4.02": "Non-Reliance on Previously Issued Financial Statements",
    "5.01": "Changes in Control of Registrant",
    "5.02": "Departure/Election of Directors or Officers",
    "5.03": "Amendments to Articles of Incorporation or Bylaws",
    "5.04": "Temporary Suspension of Trading Under Employee Benefit Plans",
    "5.05": "Amendment to Registrant's Code of Ethics",
    "5.06": "Change in Shell Company Status",
    "5.07": "Submission of Matters to a Vote of Security Holders",
    "5.08": "Shareholder Nominations",
    "6.01": "ABS Informational and Computational Material",
    "6.02": "Change of Servicer or Trustee",
    "6.03": "Change in Credit Enhancement or External Support",
    "6.04": "Failure to Make a Required Distribution",
    "6.05": "Securities Act Updating Disclosure",
    "7.01": "Regulation FD Disclosure",
    "8.01": "Other Events",
    "9.01": "Financial Statements and Exhibits",
}

# 10-K 섹션 패턴
SECTION_PATTERNS_10K = [
    (r"ITEM\s*1[.\s]+BUSINESS", "Item 1"),
    (r"ITEM\s*1A[.\s]+RISK\s*FACTORS", "Item 1A"),
    (r"ITEM\s*1B[.\s]+UNRESOLVED\s*STAFF\s*COMMENTS", "Item 1B"),
    (r"ITEM\s*2[.\s]+PROPERTIES", "Item 2"),
    (r"ITEM\s*3[.\s]+LEGAL\s*PROCEEDINGS", "Item 3"),
    (r"ITEM\s*4[.\s]+MINE\s*SAFETY", "Item 4"),
    (r"ITEM\s*5[.\s]+MARKET", "Item 5"),
    (r"ITEM\s*6[.\s]+", "Item 6"),
    (r"ITEM\s*7[.\s]+MANAGEMENT.?S\s*DISCUSSION", "Item 7"),
    (r"ITEM\s*7A[.\s]+QUANTITATIVE", "Item 7A"),
    (r"ITEM\s*8[.\s]+FINANCIAL\s*STATEMENTS", "Item 8"),
    (r"ITEM\s*9[.\s]+CHANGES", "Item 9"),
    (r"ITEM\s*9A[.\s]+CONTROLS", "Item 9A"),
    (r"ITEM\s*10[.\s]+DIRECTORS", "Item 10"),
    (r"ITEM\s*11[.\s]+EXECUTIVE\s*COMPENSATION", "Item 11"),
    (r"ITEM\s*12[.\s]+SECURITY\s*OWNERSHIP", "Item 12"),
    (r"ITEM\s*13[.\s]+CERTAIN\s*RELATIONSHIPS", "Item 13"),
    (r"ITEM\s*14[.\s]+PRINCIPAL\s*ACCOUNTANT", "Item 14"),
    (r"ITEM\s*15[.\s]+EXHIBIT", "Item 15"),
    (r"ITEM\s*16[.\s]+FORM\s*10-K\s*SUMMARY", "Item 16"),
]

# 10-Q 섹션 패턴
SECTION_PATTERNS_10Q = [
    (r"ITEM\s*1[.\s]+FINANCIAL\s*STATEMENTS", "Item 1"),
    (r"ITEM\s*2[.\s]+MANAGEMENT.?S\s*DISCUSSION", "Item 2"),
    (r"ITEM\s*3[.\s]+QUANTITATIVE", "Item 3"),
    (r"ITEM\s*4[.\s]+CONTROLS", "Item 4"),
    (r"PART\s*II", "Part II"),
    (r"ITEM\s*1[.\s]+LEGAL\s*PROCEEDINGS", "Part II Item 1"),
    (r"ITEM\s*1A[.\s]+RISK\s*FACTORS", "Part II Item 1A"),
    (r"ITEM\s*2[.\s]+UNREGISTERED\s*SALES", "Part II Item 2"),
    (r"ITEM\s*5[.\s]+OTHER\s*INFORMATION", "Part II Item 5"),
    (r"ITEM\s*6[.\s]+EXHIBITS", "Part II Item 6"),
]

# 거버넌스 패턴
GOVERNANCE_PATTERNS = [
    (r"majority\s+voting", "Majority voting for directors"),
    (r"proxy\s+access", "Proxy access"),
    (r"annual\s+election.*?directors", "Annual election of directors"),
    (r"no\s+poison\s+pill", "No poison pill"),
    (r"independent\s+(?:board\s+)?chair", "Independent board chair"),
    (r"lead\s+independent\s+director", "Lead independent director"),
    (r"clawback\s+polic", "Clawback policy"),
    (r"stock\s+ownership\s+guideline", "Stock ownership guidelines"),
    (r"no\s+hedging", "Anti-hedging policy"),
    (r"no\s+pledging", "Anti-pledging policy"),
    (r"overboarding\s+polic", "Director overboarding policy"),
    (r"board\s+diversity", "Board diversity policy"),
    (r"esg|sustainability\s+committee", "ESG/Sustainability focus"),
]

# 기관투자자 키워드
INSTITUTION_KEYWORDS = [
    "fund", "capital", "management", "partners", "advisors", 
    "investment", "blackrock", "vanguard", "state street",
    "fidelity", "schwab", "jp morgan", "goldman"
]


# ============================================================
# 파싱 유틸리티 함수
# ============================================================

def parse_currency(text: str) -> float:
    """통화 문자열을 숫자로 변환"""
    if not text:
        return 0.0
    
    text = text.replace("$", "").replace(",", "")
    text = text.replace("—", "0").replace("-", "0").replace("–", "0")
    text = text.strip()
    
    if not text:
        return 0.0
    
    try:
        return float(text)
    except ValueError:
        return 0.0


def parse_int(text: str) -> int:
    """정수 문자열을 숫자로 변환"""
    if not text:
        return 0
    
    text = text.replace(",", "").replace("$", "").strip()
    
    try:
        return int(float(text))
    except ValueError:
        return 0


def parse_percentage(text: str) -> float:
    """퍼센트 문자열을 숫자로 변환"""
    if not text:
        return 0.0
    
    match = re.search(r'([\d.]+)\s*%?', text)
    if match:
        return float(match.group(1))
    return 0.0


def clean_text(text: str) -> str:
    """텍스트 정리"""
    if not text:
        return ""
    
    # 연속 공백 및 특수문자 제거
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r"[\u200b]", " ", text)
    text = re.sub(r"[\x91]", "‘", text)
    text = re.sub(r"[\x92]", "’", text)
    text = re.sub(r"[\x93]", "“", text)
    text = re.sub(r"[\x94]", "”", text)
    text = re.sub(r"[\x95]", "•", text)
    text = re.sub(r"[\x96]", "-", text)
    text = re.sub(r"[\x97]", "-", text)
    text = re.sub(r"[\x98]", "˜", text)
    text = re.sub(r"[\x99]", "™", text)
    text = re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2015]", "-", text)
    text = re.sub(r"[\u2018]", "‘", text)
    text = re.sub(r"[\u2019]", "’", text)
    text = re.sub(r"[\u2009]", " ", text)
    text = re.sub(r"[\u00ae]", "®", text)
    text = re.sub(r"[\u201c]", "“", text)
    text = re.sub(r"[\u201d]", "”", text)
    return text.strip()


def extract_sections(text: str, patterns: list) -> dict:
    """텍스트에서 섹션 추출"""
    sections = {}
    positions = []
    
    for pattern, name in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            positions.append((match.start(), name))
    
    positions.sort(key=lambda x: x[0])
    
    for i, (pos, name) in enumerate(positions):
        end_pos = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        section_text = text[pos:end_pos].strip()
        sections[name] = section_text[:10000]
    
    return sections

def find_main_document(html_docs: list, json_docs: dict, keywords: list, doc_type: str = None) -> Optional[str]:
    """파일링에서 메인 문서 찾기"""
    items = json_docs.get("directory", {}).get("item", [])
    
    # 1. Index JSON에서 문서 타입으로 찾기
    # 2. Filing Detail Index HTML에서 문서 타입으로 찾기
    if doc_type:
        for item in items:
            if item.get("type", "").upper() == doc_type.upper():
                name = item.get("name", "")
                if name.endswith((".htm", ".html")):
                    print(f'Main document by type [{doc_type}] from JSON', name)
                    return name
        
        for item in html_docs:
            doc_type = item.get("Type", "")
            if doc_type and doc_type.upper() == doc_type.upper():
                doc_href = item.get("Document_href", "")
                if doc_href.endswith((".htm", ".html")):
                    print(f'Main document by type [{doc_type}] from HTML', doc_href)
                    return doc_href
    
    # 3. 키워드로 찾기
    # a10-kexhibit21109272025.htm <- 잘못된 매칭으로 파싱 오류 발생
    # a10-kexhibit21109272025.html -> aapl-20250927.htm 으로 매칭되어야 함
    for item in items:
        name = item.get("name", "").lower()
        if name.endswith((".htm", ".html")):
            for kw in keywords:
                if kw.lower() in name:
                    print(f'Main document by keyword [{kw}]', name)
                    return item.get("name")
    
    # 4. 가장 큰 htm 파일 선택
    htm_files = [
        item for item in items
        if item.get("name", "").endswith((".htm", ".html"))
    ]
    
    #print(htm_files)
    """
    'size'의 key가 없을 경우 0으로 처리 또한 'size' 값이 ''인 경우 0으로 처리 
    {
      'last-modified': '2025-04-17 17:08:22', 
      'name': '0001326801-25-000040-index-headers.html', 
      'type': 'text.gif', 
      'size': ''
    }
    """
    if htm_files:
        name = max(htm_files, key=lambda x: int(x.get("size", 0).replace("","0"))).get("name")
        print('Main document by size', name)
        return name
    
    return None


def is_institution(name: str) -> bool:
    """기관투자자 여부 판별"""
    name_lower = name.lower()
    return any(kw in name_lower for kw in INSTITUTION_KEYWORDS)
