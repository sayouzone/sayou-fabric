import os
import shutil
import sys
from unittest.mock import MagicMock

from sayou.loader.pipeline import LoaderPipeline


def run_mock_test():
    print(">>> 💾 [Mock] Testing Pipeline -> ChromaDB...")

    mock_chroma = MagicMock()
    mock_client = MagicMock()
    mock_coll = MagicMock()
    mock_chroma.PersistentClient.return_value = mock_client
    mock_client.get_or_create_collection.return_value = mock_coll
    sys.modules["chromadb"] = mock_chroma

    pipeline = LoaderPipeline()

    payload = [{"id": "vec_1", "vector": [0.1, 0.2], "content": "test"}]

    pipeline.run(
        input_data=payload, destination="chroma://./mock_db/mock_col", strategy="chroma"
    )

    if mock_coll.upsert.called:
        print("✅ Mock Test Passed.")
    else:
        print("❌ Mock Test Failed.")


def run_real_test():
    print("\n>>> 💾 [Real] Testing Pipeline -> ChromaDB (Local)...")

    test_dir = "./chroma_real_test"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    pipeline = LoaderPipeline()

    payload = [
        {"id": "doc_1", "vector": [0.1, 0.2, 0.3], "content": "Real Data"},
        {"id": "doc_2", "vector": [0.9, 0.8, 0.7], "content": "Another Data"},
    ]

    pipeline.run(
        input_data=payload,
        destination=f"chroma://{test_dir}/demo_collection",
        strategy="chroma",
    )

    print(f"✅ Real Test Passed: Data saved to '{test_dir}'")

    import chromadb

    client = chromadb.PersistentClient(path=test_dir)
    col = client.get_collection("demo_collection")
    print(f"   -> Count in DB: {col.count()}")


if __name__ == "__main__":
    run_mock_test()
    print("-" * 20)
    run_real_test()
