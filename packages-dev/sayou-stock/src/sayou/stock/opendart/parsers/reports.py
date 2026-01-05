import io
import zipfile
import re
import pandas as pd
from datetime import datetime
from urllib.parse import unquote

from ..client import OpenDartClient
from ..models import (
    ReportStatus,
    OpenDartRequest,
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
    quarters,
    REPORT_ITEMS,
    REPORTS_COLUMNS,
)

class OpenDartReportsParser:
    """
    OpenDART 정기보고서 주요정보 API 파싱 클래스
    
    정기보고서 주요정보 (Key Information in Periodic Reports):
    - https://opendart.fss.or.kr/guide/main.do?apiGrpCd=DS002
    """

    def __init__(self, client: OpenDartClient):
        self.client = client

    def fetch(self, corp_code: str, year: str, quarter: int, api_no: int | ReportStatus = ReportStatus.STOCK_ISSUANCE):
        if isinstance(api_no, int):
            api_no = ReportStatus(api_no)

        url = ReportStatus.url_by_code(api_no.value)

        if not url:
            return

        report_code = quarters.get(str(quarter), "4")
        
        request = OpenDartRequest(
            crtfc_key=self.client.api_key,
            corp_code=corp_code,
            bsns_year=year,
            reprt_code=report_code,
        )

        response = self.client._get(url, params=request.to_params())

        json_data = response.json()
        #print(json_data)
            
        status = json_data.get("status")

        # 에러 체크
        if status != "000":
            print(f"Error: {json_data.get('message')}")
            return []

        self.corp_code = json_data.get("corp_code")
        self.corp_name = json_data.get("corp_name")
        self.stock_code = json_data.get("stock_code")

        del json_data["status"]
        del json_data["message"]
        
        print(f"api_type: {api_no.display_name}")
        data_list = json_data.get("list", [])
        if api_no == ReportStatus.STOCK_ISSUANCE:
            return [StockIssuanceData(**data) for data in data_list]
        elif api_no == ReportStatus.DIVIDENDS:
            return [DividendsData(**data) for data in data_list]
        elif api_no == ReportStatus.TREASURY_STOCK:
            return [TreasuryStockData(**data) for data in data_list]
        elif api_no == ReportStatus.MAJOR_SHAREHOLDER:
            return [MajorShareholderData(**data) for data in data_list]
        elif api_no == ReportStatus.MAJOR_SHAREHOLDER_CHANGE:
            return [MajorShareholderChangeData(**data) for data in data_list]
        elif api_no == ReportStatus.MINOR_SHAREHOLDER:
            return [MinorShareholderData(**data) for data in data_list]
        elif api_no == ReportStatus.EXECUTIVE:
            return [ExecutiveData(**data) for data in data_list]
        elif api_no == ReportStatus.EMPLOYEE:
            return [EmployeeData(**data) for data in data_list]
        elif api_no == ReportStatus.DIRECTOR_COMPENSATION:
            return [DirectorCompensationData(**data) for data in data_list]
        elif api_no == ReportStatus.TOTAL_DIRECTOR_COMPENSATION:
            return [TotalDirectorCompensationData(**data) for data in data_list]
        elif api_no == ReportStatus.TOP5_DIRECTOR_COMPENSATION:
            return [DirectorCompensationData(**data) for data in data_list]
        elif api_no == ReportStatus.INTERCORPORATE_INVESTMENT:
            return [IntercorporateInvestmentData(**data) for data in data_list]
        elif api_no == ReportStatus.OUTSTANDING_SHARES:
            return [OutstandingSharesData(**data) for data in data_list]
        elif api_no == ReportStatus.DEBT_SECURITIES_ISSUANCE:
            return [DebtSecuritiesIssuanceData(**data) for data in data_list]
        elif api_no == ReportStatus.CP_OUTSTANDING:
            return [CPOutstandingData(**data) for data in data_list]
        elif api_no == ReportStatus.SHORT_TERM_BONDS_OUTSTANDING:
            return [ShortTermBondsOutstandingData(**data) for data in data_list]
        elif api_no == ReportStatus.CORPORATE_BONDS_OUTSTANDING:
            return [CorporateBondsOutstandingData(**data) for data in data_list]
        elif api_no == ReportStatus.HYBRID_SECURITIES_OUTSTANDING:
            return [HybridSecuritiesOutstandingData(**data) for data in data_list]
        elif api_no == ReportStatus.COCO_BONDS_OUTSTANDING:
            return [CoCoBondsOutstandingData(**data) for data in data_list]
        elif api_no == ReportStatus.AUDIT_OPINIONS:
            return [AuditOpinionsData(**data) for data in data_list]
        elif api_no == ReportStatus.AUDIT_SERVICE_CONTRACTS:
            return [AuditServiceContractsData(**data) for data in data_list]
        elif api_no == ReportStatus.NON_AUDIT_SERVICE_CONTRACTS:
            return [NonAuditServiceContractsData(**data) for data in data_list]
        elif api_no == ReportStatus.OUTSIDE_DIRECTOR_CHANGES:
            return [OutsideDirectorChangesData(**data) for data in data_list]
        elif api_no == ReportStatus.UNREGISTERED_EXECUTIVE_COMPENSATION:
            return [UnregisteredExecutiveCompensationData(**data) for data in data_list]
        elif api_no == ReportStatus.APPROVED_DIRECTOR_COMPENSATION:
            return [ApprovedDirectorCompensationData(**data) for data in data_list]
        elif api_no == ReportStatus.COMPENSATION_CATEGORY:
            return [CompensationCategoryData(**data) for data in data_list]
        elif api_no == ReportStatus.PROCEEDS_USE:
            return [ProceedsUseData(**data) for data in data_list]
        elif api_no == ReportStatus.PRIVATE_EQUITY_FUNDS_USE:
            return [PrivateEquityFundsUseData(**data) for data in data_list]

        return []
