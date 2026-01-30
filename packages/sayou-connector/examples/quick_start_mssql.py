import datetime
import json
import sys
import uuid
from decimal import Decimal
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline


# ==========================================
# [Mode 1] Mock Setup
# ==========================================
def setup_mock_mssql():
    mock_pymssql = MagicMock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    mock_pymssql.connect.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = __enter__ = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor

    fake_data = [
        {
            "EmployeeID": 101,
            "Name": "John Doe",
            "Salary": Decimal("50000.00"),
            "GlobalID": uuid.uuid4(),
            "HireDate": datetime.datetime(2020, 5, 20),
        },
        {
            "EmployeeID": 102,
            "Name": "Jane Smith",
            "Salary": Decimal("65000.50"),
            "GlobalID": uuid.uuid4(),
            "HireDate": datetime.datetime(2019, 8, 15),
        },
    ]

    mock_cursor.fetchmany.side_effect = [fake_data, []]

    sys.modules["pymssql"] = mock_pymssql


def run_mock_mssql():
    setup_mock_mssql()
    print(">>> 🏢 [Mock] Running MSSQL ETL Test...")

    OUTPUT_DIR = "./sayou_archive/mssql"

    stats = TransferPipeline().process(
        source="mssql://server/db",
        destination=OUTPUT_DIR,
        strategies={"connector": "mssql"},
        tables=["Employees"],
        connection_args={
            "server": "192.168.0.10",
            "user": "sa",
            "password": "pw",
            "dbname": "HR",
        },
    )
    print(json.dumps(stats, indent=2))


# ==========================================
# [Mode 2] Real Execution
# ==========================================
def run_real_mssql():
    print(">>> 🏢 [Real] Running MSSQL ETL...")

    OUTPUT_DIR = "./sayou_archive/mssql_real"

    DB_CONFIG = {
        "server": "10.10.10.5",  # 'MyServer\\InstanceName'
        "port": 1433,
        "user": "sa",
        "password": "StrongPassword!",
        "dbname": "LegacySystem",
    }

    stats = TransferPipeline().process(
        source="mssql://enterprise",
        destination=OUTPUT_DIR,
        strategies={"connector": "mssql"},
        connector_kwargs={
            "query": "SELECT TOP 100 * FROM LargeTransactionTable WHERE Status='Pending'",
            "connection_args": DB_CONFIG,
        },
    )
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    run_mock_mssql()
    # run_real_mssql()
