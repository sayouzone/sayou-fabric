import os
import sys
from unittest.mock import MagicMock

from sayou.loader.pipeline import LoaderPipeline


def run_mock_test():
    print(">>> 🐘 [Mock] Testing Pipeline -> Postgres...")

    mock_pg = MagicMock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_pg.connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    sys.modules["psycopg2"] = mock_pg

    pipeline = LoaderPipeline()

    payload = [
        {"id": 101, "name": "Mock Product A", "price": 1000},
        {"id": 102, "name": "Mock Product B", "price": 2000},
    ]

    try:
        pipeline.process(
            input_data=payload,
            destination="postgres://user:pass@localhost:5432/mydb",
            strategy="postgres",
            table_name="products",
            pk_columns=["id"],
        )

        if mock_cursor.executemany.called:
            print("✅ Mock Test Passed: Query generated and executed.")
            query = mock_cursor.executemany.call_args[0][0]
            print(f"   [SQL]: {query.strip()[:60]}...")
        else:
            print("❌ Mock Test Failed: No execution.")

    except Exception as e:
        print(f"❌ Mock Error: {e}")


def run_real_test():
    print("\n>>> 🐘 [Real] Testing Pipeline -> Postgres...")

    db_uri = os.getenv(
        "PG_URI", "postgresql://postgres:password@localhost:5432/test_db"
    )

    pipeline = LoaderPipeline()

    payload = [
        {"id": 1, "name": "Real Item 1", "status": "Active"},
        {
            "id": 1,
            "name": "Real Item 1 (Updated)",
            "status": "Inactive",
        },
    ]

    try:
        pipeline.process(
            input_data=payload,
            destination=db_uri,
            strategy="postgres",
            table_name="test_table",
            pk_columns=["id"],
        )
        print(f"✅ Real Test Passed: Data written to '{db_uri}'")
    except Exception as e:
        print(f"⚠️ Real Test Skipped/Failed: {e}")
        print("   (Ensure Postgres is running and table exists)")


if __name__ == "__main__":
    run_mock_test()
    # run_real_test() # 실제 DB가 있을 때 주석 해제
