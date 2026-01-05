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
    OwnershipStatus,
    OpenDartRequest,
    MajorOwnershipData,
    InsiderOwnershipData,
)
from ..utils import (
    decode_euc_kr,
    quarters,
    OWNERSHIP_COLUMNS
)

class OpenDartOwnershipParser:
    """
    OpenDART 지분공시 종합정보 API 파싱 클래스
    
    지분공시 종합정보: Comprehensive Share Ownership Information, https://opendart.fss.or.kr/guide/main.do?apiGrpCd=DS004
    """
	
    def __init__(self, client: OpenDartClient):
        self.client = client

        self.params = {
            "crtfc_key": self.client.api_key,
            "corp_code": None,
        }

    def fetch(self, corp_code: str, api_no: int | OwnershipStatus = OwnershipStatus.MAJOR_OWNERSHIP):
        if isinstance(api_no, int):
            api_no = OwnershipStatus(api_no)

        url = OwnershipStatus.url_by_code(api_no.value)
        print(api_no, url)

        if not url:
            return

        request = OpenDartRequest(
            crtfc_key=self.client.api_key,
            corp_code=corp_code,
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
        if api_no == OwnershipStatus.MAJOR_OWNERSHIP:
            return [MajorOwnershipData(**data) for data in data_list]
        elif api_no == OwnershipStatus.INSIDER_OWNERSHIP:
            return [InsiderOwnershipData(**data) for data in data_list]

        return []