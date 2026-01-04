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
 
import io
import zipfile
import re
import pandas as pd
from datetime import datetime
from urllib.parse import unquote

from ..client import OpenDartClient
from ..models import (
    MaterialFactStatus,
    OpenDartRequest,
    PutOptionData,
    BankruptcyData,
    SuspensionData,
    RestorationData,
    DissolutionData,
    PublicIssuanceData,
    UnpublicIssuanceData,
    PublicUnpublicIssuanceData,
    CapitalReductionData,
    BankruptcyProcedureData,
    LegalActData,
    OverseasListingDecisionData,
    OverseasDelistingDecisionData,
    OverseasListingData,
    OverseasDelistingData,
    CBIssuanceDecisionData,
    BWIssuanceDecisionData,
    EBIssuanceDecisionData,
    BankruptcyProcedureSuspensionData,
    CoCoBondIssuanceDecisionData,
    ShareBuybackDecisionData,
    TreasuryStockDisposalDecisionData,
    TrustAgreementAcquisitionDecisionData,
    TrustAgreementResolutionDecisionData,
    BusinessAcquisitionDecisionData,
    BusinessTransferDecisionData,
    AssetTransferDecisionData,
    OtherShareTransferDecisionData,
    EquityLinkedBondsTransferDecisionData,
    CompanyMergerDecisionData,
    CompanySpinoffDecisionData,
    CompanySpinoffMergerDecisionData,
    ShareExchangeDecisionData,
)
from ..utils import (
    decode_euc_kr,
    MATERIAL_FACTS_URLS,
    quarters,
    MATERIAL_FACTS_COLUMNS
)

class OpenDartMaterialFactsParser:
    """
    OpenDART 주요사항보고서 주요정보 API 파싱 클래스
    
    주요사항보고서 주요정보: Key Information in Reports on Material Facts, https://opendart.fss.or.kr/guide/main.do?apiGrpCd=DS005
    """

    def __init__(self, client: OpenDartClient):
        self.client = client

    def fetch(
        self, 
        corp_code: str, 
        start_date: str, 
        end_date: str, 
        api_no: int | MaterialFactStatus = MaterialFactStatus.PUT_OPTION):
        if isinstance(api_no, int):
            api_no = MaterialFactStatus(api_no)

        url = MaterialFactStatus.url_by_code(api_no.value)

        if not url:
            return

        request = OpenDartRequest(
            crtfc_key=self.client.api_key,
            corp_code=corp_code,
            bgn_de=start_date,
            end_de=end_date,
        )

        response = self.client._get(url, params=request.to_params())

        json_data = response.json()
        #print(json_data)
            
        status = json_data.get("status")

        self.corp_code = json_data.get("corp_code")
        self.corp_name = json_data.get("corp_name")
        self.stock_code = json_data.get("stock_code")

        # 에러 체크
        if status != "000":
            print(f"Error: {json_data.get('message')}")
            return json_data

        del json_data["status"]
        del json_data["message"]
        
        print(f"api_key: {api_no.display_name}")
        data_list = json_data.get("list", [])
        if api_no == MaterialFactStatus.PUT_OPTION:
            return [PutOptionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.BANKRUPTCY:
            return [BankruptcyData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.SUSPENSION:
            return [SuspensionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.RESTORATION:
            return [RestorationData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.DISSOLUTION:
            return [DissolutionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.PUBLIC_ISSUANCE:
            return [PublicIssuanceData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.UNPUBLIC_ISSUANCE:
            return [UnpublicIssuanceData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.PUBLIC_UNPUBLIC_ISSUANCE:
            return [PublicUnpublicIssuanceData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.CAPITAL_REDUCTION:
            return [CapitalReductionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.BANKRUPTCY_PROCEDURE:
            return [BankruptcyProcedureData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.LEGAL_ACT:
            return [LegalActData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.OVERSEAS_LISTING_DECISION:
            return [OverseasListingDecisionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.OVERSEAS_DELISTING_DECISION:
            return [OverseasDelistingDecisionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.OVERSEAS_LISTING:
            return [OverseasListingData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.OVERSEAS_DELISTING:
            return [OverseasDelistingData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.CB_ISSUANCE_DECISION:
            return [CBIssuanceDecisionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.BW_ISSUANCE_DECISION:
            return [BWIssuanceDecisionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.EB_ISSUANCE_DECISION:
            return [EBIssuanceDecisionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.BANKRUPTCY_PROCEDURE_SUSPENSION:
            return [BankruptcyProcedureSuspensionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.COCO_BOND_ISSUANCE_DECISION:
            return [CoCoBondIssuanceDecisionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.SHARE_BUYBACK_DECISION:
            return [ShareBuybackDecisionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.TREASURY_STOCK_DISPOSAL_DECISION:
            return [TreasuryStockDisposalDecisionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.TRUST_AGREEMENT_ACQUISITION_DECISION:
            return [TrustAgreementAcquisitionDecisionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.TRUST_AGREEMENT_RESOLUTION_DECISION:
            return [TrustAgreementResolutionDecisionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.BUSINESS_ACQUISITION_DECISION:
            return [BusinessAcquisitionDecisionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.BUSINESS_TRANSFER_DECISION:
            return [BusinessTransferDecisionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.ASSET_ACQUISITION_DECISION:
            return [AssetTransferDecisionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.ASSET_TRANSFER_DECISION:
            return [AssetTransferDecisionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.OTHER_SHARE_ACQUISITION_DECISION:
            return [OtherShareTransferDecisionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.OTHER_SHARE_TRANSFER_DECISION:
            return [OtherShareTransferDecisionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.EQUITY_LINKED_BOND_ACQUISITION_DECISION:
            return [EquityLinkedBondsTransferDecisionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.EQUITY_LINKED_BOND_TRANSFER_DECISION:
            return [EquityLinkedBondsTransferDecisionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.COMPANY_MERGER_DECISION:
            return [CompanyMergerDecisionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.COMPANY_SPINOFF_DECISION:
            return [CompanySpinoffDecisionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.COMPANY_SPINOFF_MERGER_DECISION:
            return [CompanySpinoffMergerDecisionData(**data) for data in data_list]
        elif api_no == MaterialFactStatus.SHARE_EXCHANGE_DECISION:
            return [ShareExchangeDecisionData(**data) for data in data_list]

        return json_data