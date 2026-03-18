import datetime
import json
import sys
import uuid
from decimal import Decimal
from unittest.mock import MagicMock

from sayou.brain.pipelines.transfer import TransferPipeline


def setup_mock_postgres():
    """psycopg2 모듈 Mocking"""
    mock_pg = MagicMock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    mock_pg.connect.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor

    fake_data_batch_1 = [
        {
            "id": uuid.uuid4(),
            "price": Decimal("10.50"),
            "created_at": datetime.datetime.now(),
            "name": "Product A",
        },
        {
            "id": uuid.uuid4(),
            "price": Decimal("99.99"),
            "created_at": datetime.datetime.now(),
            "name": "Product B",
        },
    ]

    mock_cursor.fetchmany.side_effect = [fake_data_batch_1, []]

    sys.modules["psycopg2"] = mock_pg
    sys.modules["psycopg2.extras"] = MagicMock()


def run_postgres_mock_etl():
    setup_mock_postgres()
    print(">>> 🧪 Running Mock Postgres ETL...")

    OUTPUT_DIR = "./sayou_archive/postgres"

    stats = TransferPipeline().process(
        source="postgres://localhost:5432/mydb",
        destination=OUTPUT_DIR,
        strategies={"connector": "postgres"},
        tables=["products"],
        connection_args={
            "dbname": "mydb",
            "user": "user",
            "password": "pw",
            "host": "localhost",
        },
    )

    print("\n📊 Execution Result:")
    print(json.dumps(stats, indent=2))

    if stats["written"] > 0:
        print(f"\n✅ Logic Verified! Check '{OUTPUT_DIR}'")
    else:
        print("\n❌ Logic Fail.")


if __name__ == "__main__":
    run_postgres_mock_etl()
