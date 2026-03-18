import datetime
import json
import sys
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline


# ==========================================
# [Mode 1] Mock Setup
# ==========================================
def setup_mock_mysql():
    mock_pymysql = MagicMock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    mock_pymysql.connect.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = __enter__ = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    mock_pymysql.cursors.DictCursor = "DictCursor"

    fake_data = [
        {
            "id": 1,
            "username": "user_a",
            "points": 100,
            "joined_at": datetime.datetime(2023, 1, 1),
        },
        {
            "id": 2,
            "username": "user_b",
            "points": 250,
            "joined_at": datetime.datetime(2023, 1, 2),
        },
    ]

    mock_cursor.fetchmany.side_effect = [fake_data, []]

    sys.modules["pymysql"] = mock_pymysql
    sys.modules["pymysql.cursors"] = mock_pymysql.cursors


def run_mock_mysql():
    setup_mock_mysql()
    print(">>> 🐬 [Mock] Running MySQL ETL Test...")

    OUTPUT_DIR = "./sayou_archive/mysql"

    stats = TransferPipeline().process(
        source="mysql://localhost/test_db",
        destination=OUTPUT_DIR,
        strategies={"connector": "mysql"},
        tables=["users"],
        connection_args={
            "host": "localhost",
            "user": "root",
            "password": "pw",
            "dbname": "test_db",
        },
    )
    print(json.dumps(stats, indent=2))


# ==========================================
# [Mode 2] Real Execution
# ==========================================
def run_real_mysql():
    print(">>> 🐬 [Real] Running MySQL ETL...")

    OUTPUT_DIR = "./sayou_archive/mysql"

    DB_CONFIG = {
        "host": "127.0.0.1",
        "port": 3306,
        "user": "admin",
        "password": "real_password",
        "dbname": "service_prod",
    }

    stats = TransferPipeline().process(
        source="mysql://production",
        destination=OUTPUT_DIR,
        strategies={"connector": "mysql"},
        tables=["orders", "products"],
        connection_args=DB_CONFIG,
    )
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    run_mock_mysql()
    # run_real_mysql()
