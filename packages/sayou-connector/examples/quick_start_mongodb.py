import datetime
import json
import sys
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline


def run_mongo_test(mock=True):
    print(f"\n>>> 🍃 Running MongoDB Test (Mock={mock})")

    OUTPUT_DIR = "./sayou_archive/mongodb"

    if mock:
        mock_pymongo = MagicMock()
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_col = MagicMock()

        sys.modules["pymongo"] = mock_pymongo
        sys.modules["bson"] = MagicMock()

        mock_pymongo.MongoClient.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_col

        mock_col.find.return_value.limit.return_value = [
            {
                "_id": "mock_obj_id",
                "title": "Mongo Doc 1",
                "created": datetime.datetime.now(),
            },
            {"_id": "mock_obj_id_2", "title": "Mongo Doc 2"},
        ]

    stats = TransferPipeline().process(
        source="mongodb://localhost",
        destination=OUTPUT_DIR,
        strategies={"connector": "mongodb"},
        collections=["logs", "users"],
        connection_args={"host": "localhost", "dbname": "test_db"},
    )
    print(json.dumps(stats, indent=2))


def run_real_mongo():
    print(">>> 🍃 [Real] Running MongoDB ETL...")

    DB_CONFIG = {
        "host": "localhost",
        "port": 27017,
        "dbname": "test_db",
        # "user": "admin",
        # "password": "pass"
    }

    # 2. 가져올 컬렉션
    TARGET_COLLECTIONS = ["users", "logs"]

    stats = TransferPipeline().process(
        source="mongodb://localhost",
        destination="./archive_mongo_real",
        strategies={"connector": "mongodb"},
        connector_kwargs={
            "collections": TARGET_COLLECTIONS,
            "connection_args": DB_CONFIG,
            # "query": {"status": "active"}
        },
    )

    print("\n📊 MongoDB Execution Result:")
    print(json.dumps(stats, indent=2))

    if stats["written"] > 0:
        print(f"\n✅ Success! Data saved to './archive_mongo_real'")
    else:
        print("\n⚠️ 0 documents fetched. Check if the collection is empty.")


if __name__ == "__main__":
    run_mongo_test(mock=True)
