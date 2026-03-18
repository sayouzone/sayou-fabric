import datetime
import json
import os
import sys
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline


def setup_mock_oracle():
    mock_oracledb = MagicMock()

    # 1. Connection
    mock_conn = MagicMock()
    mock_oracledb.connect.return_value = __enter__ = mock_conn
    mock_conn.__enter__.return_value = mock_conn

    # 2. Cursor
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = __enter__ = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor

    mock_cursor.description = [("ID",), ("NAME",), ("REG_DATE",)]
    mock_cursor.fetchmany.side_effect = [
        [
            (101, "Alice", datetime.datetime(2024, 1, 1, 10, 0)),
            (102, "Bob", datetime.datetime(2024, 1, 2, 11, 0)),
        ],
        [],
    ]

    sys.modules["oracledb"] = mock_oracledb
    return mock_oracledb


def run_oracle_mock_etl():
    setup_mock_oracle()

    print(">>> 🧪 Running Mock Oracle ETL (No Real DB Required)...")

    OUTPUT_DIR = "./sayou_archive/oracle"

    stats = TransferPipeline().process(
        source="oracle://127.0.0.1:1521/XE",
        destination=OUTPUT_DIR,
        strategies={"connector": "oracle"},
        tables=["TEST_USER_TB"],
        connection_args={
            "user": "mock_user",
            "password": "mock_password",
            "host": "127.0.0.1",
            "port": 1521,
            "service_name": "XE",
        },
    )

    print("\n📊 Mock Execution Result:")
    print(json.dumps(stats, indent=2))

    if stats["written"] > 0:
        print(f"\n✅ Logic Verified! (Simulated data saved to '{OUTPUT_DIR}')")
        sample_file = os.path.join(OUTPUT_DIR, "oracle_TEST_USER_TB_0.json")
    else:
        print("\n❌ Something went wrong in logic.")


def run_oracle_etl():
    OUTPUT_DIR = "./sayou_archive/oracle_real"

    DB_CONFIG = {
        "user": "USER",  # 변경 필요
        "password": "PASS",  # 변경 필요
        "host": "HOST",  # 변경 필요
        "port": PORT,
        "service_name": "SERVICE_NAME",  # 변경 필요
    }

    TARGET_TABLES = ["TABLE_NAME"]

    print(f">>> 🚀 Starting Oracle ETL for tables: {TARGET_TABLES}")

    stats = TransferPipeline().process(
        source=f"oracle://{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['service_name']}",
        destination=OUTPUT_DIR,
        strategies={"connector": "oracle"},
        connector_kwargs={
            "tables": TARGET_TABLES,
            "connection_args": DB_CONFIG,
            # "query": "SELECT * FROM EMP WHERE SAL > 1000",
            # "tables": []
        },
    )

    print("\n📊 Execution Result:")
    print(json.dumps(stats, indent=2))

    if stats["written"] > 0:
        print(f"\n✅ Success! Check '{OUTPUT_DIR}' folder.")
    else:
        print("\n❌ No data collected. Check connection args and firewalls.")


if __name__ == "__main__":
    run_oracle_mock_etl()
