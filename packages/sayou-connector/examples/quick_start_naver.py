import json
import sys
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline


def run_naver_test(mock=True):
    print(f"\n>>> 🇳 Running Naver Search Test (Mock={mock})")

    OUTPUT_DIR = "./sayou_archive/naver"

    if mock:
        mock_requests = MagicMock()
        sys.modules["requests"] = mock_requests

        mock_resp = MagicMock()
        mock_requests.get.return_value = mock_resp
        mock_resp.json.return_value = {
            "items": [
                {
                    "title": "Sayou <b>Platform</b> Review",
                    "link": "https://blog.naver.com/...",
                },
                {"title": "Python RAG Tutorial", "link": "https://cafe.naver.com/..."},
            ]
        }

    stats = TransferPipeline().process(
        source="naver://search",
        destination=OUTPUT_DIR,
        strategies={"connector": "naver"},
        query="Sayou Fabric",
        categories=["blog", "news"],
        auth={
            "client_id": "YOUR_NAVER_ID",
            "client_secret": "YOUR_NAVER_SECRET",
        },
    )
    print(json.dumps(stats, indent=2))


def run_real_naver():
    print(">>> 🇳 [Real] Running Naver Search ETL...")

    # 1. 네이버 API 키 입력 (개발자 센터 발급)
    NAVER_AUTH = {
        "client_id": "YOUR_REAL_CLIENT_ID",  # <--- 여기에 입력
        "client_secret": "YOUR_REAL_SECRET",  # <--- 여기에 입력
    }

    # 키가 없는 경우 실행 방지
    if NAVER_AUTH["client_id"] == "YOUR_REAL_CLIENT_ID":
        print("❌ Error: Please input your real Naver Client ID/Secret in the code.")
        return

    stats = TransferPipeline().process(
        source="naver://search",
        destination="./archive_naver_real",
        strategies={"connector": "naver"},
        connector_kwargs={
            "query": "인공지능 RAG 트렌드",  # 검색어
            "categories": ["blog", "news"],  # 검색 대상
            "auth": NAVER_AUTH,
        },
    )

    print("\n📊 Naver Search Execution Result:")
    print(json.dumps(stats, indent=2))

    if stats["written"] > 0:
        print(f"\n✅ Success! Data saved to './archive_naver_real'")


if __name__ == "__main__":
    run_naver_test(mock=True)
