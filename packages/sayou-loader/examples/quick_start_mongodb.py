import sys
from unittest.mock import MagicMock


def run_mock_test():
    print(">>> 🍃 [Mock] Testing Pipeline -> MongoDB...")

    # --- 1. Mock Setup ---
    mock_pymongo = MagicMock()
    mock_col = MagicMock()
    # 체이닝: MongoClient -> db -> collection
    mock_pymongo.MongoClient.return_value.__getitem__.return_value.__getitem__.return_value = (
        mock_col
    )
    mock_col.bulk_write.return_value.matched_count = 1
    sys.modules["pymongo"] = mock_pymongo

    # --- 2. Pipeline Execution ---
    from sayou.loader.pipeline import LoaderPipeline

    pipeline = LoaderPipeline()

    payload = [{"id": "log_a", "msg": "test"}, {"id": "log_b", "msg": "test2"}]

    try:
        pipeline.run(
            input_data=payload,
            destination="mongodb://localhost:27017",
            strategy="mongodb",
            dbname="test_db",
            collection="test_col",
        )

        if mock_col.bulk_write.called:
            print("✅ Mock Test Passed: bulk_write called.")
        else:
            print("❌ Mock Test Failed.")

    except Exception as e:
        print(f"❌ Mock Error: {e}")


def run_real_test():
    print("\n>>> 🍃 [Real] Testing Pipeline -> MongoDB...")

    from sayou.loader.pipeline import LoaderPipeline

    pipeline = LoaderPipeline()

    try:
        pipeline.run(
            input_data=[{"id": "real_1", "ts": "2024-01-01"}],
            destination="mongodb://localhost:27017",
            strategy="mongodb",
            dbname="sayou_demo",
            collection="logs",
        )
        print("✅ Real Test Passed.")
    except Exception as e:
        print(f"⚠️ Real Test Skipped/Failed: {e}")


if __name__ == "__main__":
    run_mock_test()
    # run_real_test()
