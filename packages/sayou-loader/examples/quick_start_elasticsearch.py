import sys
from unittest.mock import MagicMock

from sayou.loader.pipeline import LoaderPipeline


def run_mock_test():
    print(">>> 🔍 [Mock] Testing Pipeline -> Elasticsearch...")

    # --- 1. Mock Setup ---
    mock_es = MagicMock()
    mock_helpers = MagicMock()
    mock_client = MagicMock()

    mock_es.Elasticsearch.return_value = mock_client
    mock_client.ping.return_value = True
    mock_helpers.bulk.return_value = (1, 0)

    mock_es.helpers = mock_helpers
    sys.modules["elasticsearch"] = mock_es
    sys.modules["elasticsearch.helpers"] = mock_helpers

    pipeline = LoaderPipeline()

    payload = [{"id": "doc_1", "title": "Mock Search"}]

    try:
        pipeline.run(
            input_data=payload,
            destination="http://localhost:9200",
            strategy="elasticsearch",
            index_name="test_index",
        )

        if mock_helpers.bulk.called:
            print("✅ Mock Test Passed: helpers.bulk called.")
        else:
            print("❌ Mock Test Failed.")

    except Exception as e:
        print(f"❌ Mock Error: {e}")


def run_real_test():
    print("\n>>> 🔍 [Real] Testing Pipeline -> Elasticsearch...")

    pipeline = LoaderPipeline()

    try:
        pipeline.run(
            input_data=[{"id": "real_doc", "text": "Hello ES"}],
            destination="http://localhost:9200",
            strategy="elasticsearch",
            index_name="sayou_test",
        )
        print("✅ Real Test Passed.")
    except Exception as e:
        print(f"⚠️ Real Test Skipped/Failed: {e}")


if __name__ == "__main__":
    run_mock_test()
    # run_real_test()
