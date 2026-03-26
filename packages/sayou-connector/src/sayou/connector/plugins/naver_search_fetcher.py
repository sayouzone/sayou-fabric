from typing import Any, Dict, List

import requests
from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher


# ---------------------------------------------------------
# Fetcher
# ---------------------------------------------------------
@register_component("fetcher")
class NaverSearchFetcher(BaseFetcher):
    """
    Naver Search API Fetcher.
    Uses Requests to fetch search results from Naver OpenAPI.
    """

    component_name = "NaverSearchFetcher"
    SUPPORTED_TYPES = ["naver"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if "naver" in uri.lower() else 0.0

    def _do_fetch(self, task: SayouTask) -> List[Dict[str, Any]]:
        params = task.params
        category = params.get("category", "blog")
        query = params.get("query")
        auth = params.get("auth", {})

        client_id = auth.get("client_id")
        client_secret = auth.get("client_secret")

        if not client_id or not client_secret:
            raise ValueError("[NaverFetcher] Client ID and Secret are required.")

        # API URL (JSON format)
        url = f"https://openapi.naver.com/v1/search/{category}.json"

        headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret,
        }

        # display=100 (Max), sort=sim (sim/date)
        req_params = {"query": query, "display": 100, "start": 1, "sort": "sim"}

        self._log(f"Searching Naver [{category}]: {query}")

        try:
            resp = requests.get(url, headers=headers, params=req_params)
            resp.raise_for_status()
            data = resp.json()
            return data.get("items", [])

        except Exception as e:
            self._log(f"Naver API Error: {e}", level="error")
            raise e
