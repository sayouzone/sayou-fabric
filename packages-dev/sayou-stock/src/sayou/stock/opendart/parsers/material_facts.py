import io
import zipfile
import re
import pandas as pd
from datetime import datetime
from urllib.parse import unquote

from ..client import OpenDartClient

from ..utils import (
    decode_euc_kr,
    material_facts_urls,
    quarters
)

class DartMaterialFactsParser:
    """
    OpenDART 주요사항보고서 주요정보 API 파싱 클래스
    
    주요사항보고서 주요정보: Key Information in Reports on Material Facts, https://opendart.fss.or.kr/guide/main.do?apiGrpCd=DS005
    """

    def __init__(self, client: OpenDartClient):
        self.client = client

        self.params = {
            "crtfc_key": self.client.api_key,
            "corp_code": None,
            "bgn_de": None,
            "end_de": None,
        }

    def fetch(self, corp_code: str, start_date: str, end_date: str, api_no: int = -1, api_type: str = None):
        url = None

        api_key = list(material_facts_urls.keys())[api_no] if api_no > -1 else api_type        
        url = material_facts_urls.get(api_key)

        if not url:
            return
        
        self.params["corp_code"] = corp_code
        self.params["bgn_de"] = start_date
        self.params["end_de"] = end_date

        response = self.client._get(url, params=self.params)

        json_data = response.json()
        print(json_data)
            
        status = json_data.get("status")

        # 에러 체크
        if status != "000":
            print(f"Error: {json_data.get('message')}")
            return api_key, json_data

        self.corp_code = json_data.get("corp_code")
        self.corp_name = json_data.get("corp_name")
        self.stock_code = json_data.get("stock_code")

        return api_key, json_data