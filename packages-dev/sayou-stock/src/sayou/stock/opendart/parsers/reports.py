import io
import zipfile
import re
import pandas as pd
from datetime import datetime
from urllib.parse import unquote

from ..client import OpenDartClient

from ..utils import (
    decode_euc_kr,
    reports_urls,
    quarters
)

class DartReportsParser:
    """
    OpenDART 정기보고서 주요정보 API 파싱 클래스
    
    정기보고서 주요정보: Key Information in Periodic Reports, https://opendart.fss.or.kr/guide/main.do?apiGrpCd=DS002
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

        api_key = list(reports_urls.keys())[api_no] if api_no > -1 else api_type        
        url = reports_urls.get(api_key)

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

        self.corp_code = json_data.get("corp_code")
        self.corp_name = json_data.get("corp_name")
        self.stock_code = json_data.get("stock_code")

        return api_key, json_data
