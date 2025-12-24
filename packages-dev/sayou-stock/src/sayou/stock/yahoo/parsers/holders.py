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
 
import logging
import pandas as pd
from typing import Any

from ..client import YahooClient
from ..utils import (
    _QUOTE_SUMMARY_URL_,
    _QUERY2_URL_
)
from .quote import YahooQuoteParser

logger = logging.getLogger(__name__)

class YahooHoldersParser:

    """
    

    https://github.com/ranaroussi/yfinance/blob/main/yfinance/scrapers/holders.py
    """

    MODULES = [
        "institutionOwnership", 
        "fundOwnership", 
        "majorDirectHolders", 
        "majorHoldersBreakdown", 
        "insiderTransactions", 
        "insiderHolders", 
        "netSharePurchaseActivity"
    ]

    OWNERSHIP_COLUMNS = {
        "reportDate": "Date Reported", 
        "organization": "Holder", 
        "position": "Shares",
        "value": "Value"
    }

    HOLDERS_COLUMNS = {
        "reportDate": "Date Reported", 
        "organization": "Holder", 
        "positionDirect": "Shares", 
        "valueDirect": "Value"
    }

    INSIDER_TRANSACTION_COLUMNS = {
        "startDate": "Start Date",
        "filerName": "Insider",
        "filerRelation": "Position",
        "filerUrl": "URL",
        "moneyText": "Transaction",
        "transactionText": "Text",
        "shares": "Shares",
        "value": "Value",
        "ownership": "Ownership"  # ownership flag, direct or institutional
    }

    INSIDER_HOLDERS_COLUMNS = {
        "name": "Name",
        "relation": "Position",
        "url": "URL",
        "transactionDescription": "Most Recent Transaction",
        "latestTransDate": "Latest Transaction Date",
        "positionDirectDate": "Position Direct Date",
        "positionDirect": "Shares Owned Directly",
        "positionIndirectDate": "Position Indirect Date",
        "positionIndirect": "Shares Owned Indirectly"
    }

    def __init__(self, client: YahooClient):
        self.client = client
        self._crumb: Optional[str] = None

        self.quote_parser = YahooQuoteParser(self.client)

    def fetch_holders(self, ticker: str):
        """

        """
        params={
            "modules": ",".join(self.MODULES), 
            "corsDomain": "finance.yahoo.com", 
            "formatted": "false", 
            "symbol": ticker
        }

        url = f"{_QUOTE_SUMMARY_URL_}/{ticker}"

        if _QUERY2_URL_ in url:
            params["crumb"] = self.quote_parser.fetch_crumb()
        
        response = self.client._get(url, params=params)
        holders_info = response.json()
        
        result = holders_info.get("quoteSummary", {}).get("result", [{}])[0]
        institution_ownership = result.get("institutionOwnership", {})
        fund_ownership = result.get("fundOwnership", {})
        major_direct_holders = result.get("majorDirectHolders", {})
        major_holders_breakdown = result.get("majorHoldersBreakdown", {})
        insider_transactions = result.get("insiderTransactions", {})
        insider_holders = result.get("insiderHolders", {})
        net_share_purchase_activity = result.get("netSharePurchaseActivity", {})

        return {
            "institutionOwnership": self._parse_ownership(institution_ownership),
            "fundOwnership": self._parse_ownership(fund_ownership),
            "majorDirectHolders": self._parse_holders(major_direct_holders),
            "majorHoldersBreakdown": self._parse_breakdown(major_holders_breakdown),
            "insiderTransactions": self._parse_insider_transactions(insider_transactions),
            "insiderHolders": self._parse_insider_holders(insider_holders),
            "netSharePurchaseActivity": self._parse_net_share_purchase_activity(net_share_purchase_activity)
        }

    def _parse_ownership(self, data: dict[str, Any]) -> dict[str, str]:
        """
        institutionOwnership
        """
        holders = data.get("ownershipList", [])
        for owner in holders:
            for k, v in owner.items():
                owner[k] = self._parse_raw_values(v)
            del owner["maxAge"]
        df = pd.DataFrame(holders)
        if not df.empty:
            df["reportDate"] = pd.to_datetime(df["reportDate"], unit="s")
            df.rename(columns=self.OWNERSHIP_COLUMNS, inplace=True)  # "pctHeld": "% Out"
        return df

    def _parse_holders(self, data: dict[str, Any]) -> dict[str, str]:
        """
        majorDirectHolders
        majorHoldersBreakdown
        """
        holders = data.get("holders", [])
        for owner in holders:
            for k, v in owner.items():
                owner[k] = self._parse_raw_values(v)
            del owner["maxAge"]
        df = pd.DataFrame(holders)
        if not df.empty:
            df["reportDate"] = pd.to_datetime(df["reportDate"], unit="s")
            df.rename(columns=self.HOLDERS_COLUMNS, inplace=True)  # "pctHeld": "% Out"
        return df

    def _parse_breakdown(self, data: dict[str, Any]) -> dict[str, str]:
        """
        majorHoldersBreakdown
        """
        if "maxAge" in data:
            del data["maxAge"]
        df = pd.DataFrame.from_dict(data, orient="index")
        if not df.empty:
            df.columns.name = "Breakdown"
            df.rename(columns={df.columns[0]: 'Value'}, inplace=True)
        return df

    def _parse_insider_transactions(self, data: dict[str, Any]) -> dict[str, str]:
        """
        majorDirectHolders
        """
        transactions = data.get("transactions", {})
        for transaction in transactions:
            for k, v in transaction.items():
                transaction[k] = self._parse_raw_values(v)
            del transaction["maxAge"]
        df = pd.DataFrame(transactions)
        if not df.empty:
            df["startDate"] = pd.to_datetime(df["startDate"], unit="s")
            df.rename(columns=self.INSIDER_TRANSACTION_COLUMNS, inplace=True)
        return df

    def _parse_insider_holders(self, data: dict[str, Any]) -> dict[str, str]:
        """
        majorDirectHolders
        """
        holders = data.get("holders", {})
        for owner in holders:
            for k, v in owner.items():
                owner[k] = self._parse_raw_values(v)
            del owner["maxAge"]
        df = pd.DataFrame(holders)
        if not df.empty:
            if "positionDirectDate" in df:
                df["positionDirectDate"] = pd.to_datetime(df["positionDirectDate"], unit="s")
            if "latestTransDate" in df:
                df["latestTransDate"] = pd.to_datetime(df["latestTransDate"], unit="s")

            df.rename(columns=self.INSIDER_HOLDERS_COLUMNS, inplace=True)
            df["Name"] = df["Name"].astype(str)
            df["Position"] = df["Position"].astype(str)
            df["URL"] = df["URL"].astype(str)
            df["Most Recent Transaction"] = df["Most Recent Transaction"].astype(str)
        return df

    def _parse_net_share_purchase_activity(self, data: dict[str, Any]):
        df = pd.DataFrame(
            {
                "Insider Purchases Last " + data.get("period", ""): [
                    "Purchases",
                    "Sales",
                    "Net Shares Purchased (Sold)",
                    "Total Insider Shares Held",
                    "% Net Shares Purchased (Sold)",
                    "% Buy Shares",
                    "% Sell Shares"
                ],
                "Shares": [
                    data.get('buyInfoShares'),
                    data.get('sellInfoShares'),
                    data.get('netInfoShares'),
                    data.get('totalInsiderShares'),
                    data.get('netPercentInsiderShares'),
                    data.get('buyPercentInsiderShares'),
                    data.get('sellPercentInsiderShares')
                ],
                "Trans": [
                    data.get('buyInfoCount'),
                    data.get('sellInfoCount'),
                    data.get('netInfoCount'),
                    pd.NA,
                    pd.NA,
                    pd.NA,
                    pd.NA
                ]
            }
        ).convert_dtypes()
        return df

    @staticmethod
    def _parse_raw_values(data):
        if isinstance(data, dict) and "raw" in data:
            return data["raw"]
        return data
