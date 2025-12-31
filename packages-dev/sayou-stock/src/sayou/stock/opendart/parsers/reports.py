import io
import zipfile
import re
import pandas as pd
from datetime import datetime
from urllib.parse import unquote

from ..client import OpenDartClient
from ..models import (
    StockIssuanceData,
    DividendsData,
    TreasuryStockData,
    MajorShareholderData,
    MajorShareholderChangeData,
    MinorShareholderData,
    ExecutiveData,
    EmployeeData,
    DirectorCompensationData,
    TotalDirectorCompensationData,
    IntercorporateInvestmentData,
    OutstandingSharesData,
    DebtSecuritiesIssuanceData,
    CPOutstandingData,
    ShortTermBondsOutstandingData,
    CorporateBondsOutstandingData,
    HybridSecuritiesOutstandingData,
    CoCoBondsOutstandingData,
    AuditOpinionsData,
    AuditServiceContractsData,
    NonAuditServiceContractsData,
    OutsideDirectorChangesData,
    UnregisteredExecutiveCompensationData,
    ApprovedDirectorCompensationData,
    CompensationCategoryData,
    ProceedsUseData,
    PrivateEquityFundsUseData,
)
from ..utils import (
    decode_euc_kr,
    REPORTS_URLS,
    quarters,
    REPORTS_COLUMNS
)

class DartReportsParser:
    """
    OpenDART 정기보고서 주요정보 API 파싱 클래스
    
    정기보고서 주요정보 (Key Information in Periodic Reports):
    - https://opendart.fss.or.kr/guide/main.do?apiGrpCd=DS002
    """

    def __init__(self, client: OpenDartClient):
        self.client = client

        self.params = {
            "crtfc_key": self.client.api_key,
            "corp_code": None,
            "bsns_year": None,
            "reprt_code": "11011",
        }

    def fetch(self, corp_code: str, year: str, quarter: int, api_no: int = -1, api_type: str = None):
        url = None

        api_key = list(REPORTS_URLS.keys())[api_no] if api_no > -1 else api_type        
        url = REPORTS_URLS.get(api_key)

        if not url:
            return

        report_code = quarters.get(str(quarter), "4")
        
        self.params["corp_code"] = corp_code
        self.params["bsns_year"] = year
        self.params["reprt_code"] = report_code

        response = self.client._get(url, params=self.params)

        json_data = response.json()
        #print(json_data)
            
        status = json_data.get("status")

        # 에러 체크
        if status != "000":
            print(f"Error: {json_data.get('message')}")
            return {}

        del json_data["status"]
        del json_data["message"]
        
        print(f"api_key: {api_key}")
        if api_key == "증자(감자) 현황":
            data_list = json_data.get("list", [])
            issuances = [StockIssuanceData(**data) for data in data_list]
            print(issuances)
        elif api_key == "배당에 관한 사항":
            data_list = json_data.get("list", [])
            dividends = [DividendsData(**data) for data in data_list]
            print(dividends)
        elif api_key == "자기주식 취득 및 처분 현황":
            data_list = json_data.get("list", [])
            treasuries = [TreasuryStockData(**data) for data in data_list]
            print(treasuries)
        elif api_key == "최대주주 현황":
            data_list = json_data.get("list", [])
            major_shareholders = [MajorShareholderData(**data) for data in data_list]
            print(major_shareholders)
        elif api_key == "최대주주 변동현황":
            data_list = json_data.get("list", [])
            major_shareholder_changes = [MajorShareholderChangeData(**data) for data in data_list]
            print(major_shareholder_changes)
        elif api_key == "소액주주 현황":
            data_list = json_data.get("list", [])
            minor_shareholders = [MinorShareholderData(**data) for data in data_list]
            print(minor_shareholders)
        elif api_key == "임원 현황":
            data_list = json_data.get("list", [])
            executives = [ExecutiveData(**data) for data in data_list]
            print(executives)
        elif api_key == "직원 현황":
            data_list = json_data.get("list", [])
            employees = [EmployeeData(**data) for data in data_list]
            print(employees)
        elif api_key == "이사·감사의 개인별 보수현황(5억원 이상)":
            data_list = json_data.get("list", [])
            director_compensations = [DirectorCompensationData(**data) for data in data_list]
            print(director_compensations)
        elif api_key == "이사·감사 전체의 보수현황(보수지급금액 - 이사·감사 전체)":
            data_list = json_data.get("list", [])
            total_director_compensations = [TotalDirectorCompensationData(**data) for data in data_list]
            print(total_director_compensations)
        elif api_key == "개인별 보수지급 금액(5억이상 상위5인)":
            data_list = json_data.get("list", [])
            top5_director_compensations = [DirectorCompensationData(**data) for data in data_list]
            print(top5_director_compensations)
        elif api_key == "타법인 출자현황":
            data_list = json_data.get("list", [])
            intercorporate_investments = [IntercorporateInvestmentData(**data) for data in data_list]
            print(intercorporate_investments)
        elif api_key == "주식의 총수 현황":
            data_list = json_data.get("list", [])
            outstanding_shares = [OutstandingSharesData(**data) for data in data_list]
            print(outstanding_shares)
        elif api_key == "채무증권 발행실적":
            data_list = json_data.get("list", [])
            debt_securities_issuances = [DebtSecuritiesIssuanceData(**data) for data in data_list]
            print(debt_securities_issuances)
        elif api_key == "기업어음증권 미상환 잔액":
            data_list = json_data.get("list", [])
            cp_outstandings = [CPOutstandingData(**data) for data in data_list]
            print(cp_outstandings)
        elif api_key == "단기사채 미상환 잔액":
            data_list = json_data.get("list", [])
            short_term_bonds_outstandings = [ShortTermBondsOutstandingData(**data) for data in data_list]
            print(short_term_bonds_outstandings)
        elif api_key == "회사채 미상환 잔액 ":
            data_list = json_data.get("list", [])
            corporate_bonds_outstandings = [CorporateBondsOutstandingData(**data) for data in data_list]
            print(corporate_bonds_outstandings)
        elif api_key == "신종자본증권 미상환 잔액":
            data_list = json_data.get("list", [])
            hybrid_securities_outstandings = [HybridSecuritiesOutstandingData(**data) for data in data_list]
            print(hybrid_securities_outstandings)
        elif api_key == "조건부 자본증권 미상환 잔액":
            data_list = json_data.get("list", [])
            co_co_bonds_outstandings = [CoCoBondsOutstandingData(**data) for data in data_list]
            print(co_co_bonds_outstandings)
        elif api_key == "회계감사인의 명칭 및 감사의견":
            data_list = json_data.get("list", [])
            audit_opinions = [AuditOpinionsData(**data) for data in data_list]
            print(audit_opinions)
        elif api_key == "감사용역체결현황":
            data_list = json_data.get("list", [])
            audit_service_contracts = [AuditServiceContractsData(**data) for data in data_list]
            print(audit_service_contracts)
        elif api_key == "회계감사인과의 비감사용역 계약체결 현황":
            data_list = json_data.get("list", [])
            non_audit_service_contracts = [NonAuditServiceContractsData(**data) for data in data_list]
            print(non_audit_service_contracts)
        elif api_key == "사외이사 및 그 변동현황":
            data_list = json_data.get("list", [])
            outside_director_changes = [OutsideDirectorChangesData(**data) for data in data_list]
            print(outside_director_changes)
        elif api_key == "미등기임원 보수현황":
            data_list = json_data.get("list", [])
            unregistered_executive_compensations = [UnregisteredExecutiveCompensationData(**data) for data in data_list]
            print(unregistered_executive_compensations)
        elif api_key == "이사·감사 전체의 보수현황(주주총회 승인금액)":
            data_list = json_data.get("list", [])
            approved_director_compensations = [ApprovedDirectorCompensationData(**data) for data in data_list]
            print(approved_director_compensations)
        elif api_key == "이사·감사 전체의 보수현황(보수지급금액 - 유형별)":
            data_list = json_data.get("list", [])
            compensation_categories = [CompensationCategoryData(**data) for data in data_list]
            print(compensation_categories)
        elif api_key == "공모자금의 사용내역":
            data_list = json_data.get("list", [])
            proceeds_uses = [ProceedsUseData(**data) for data in data_list]
            print(proceeds_uses)
        elif api_key == "사모자금의 사용내역":
            data_list = json_data.get("list", [])
            private_equity_funds_uses = [PrivateEquityFundsUseData(**data) for data in data_list]
            print(private_equity_funds_uses)

        self.corp_code = json_data.get("corp_code")
        self.corp_name = json_data.get("corp_name")
        self.stock_code = json_data.get("stock_code")

        return api_key, json_data
