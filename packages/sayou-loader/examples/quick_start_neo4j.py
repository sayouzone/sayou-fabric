import sys
from unittest.mock import MagicMock

from sayou.loader.pipeline import LoaderPipeline


def run_mock_test():
    print(">>> 🕸️ [Mock] Testing Pipeline -> Neo4j...")

    mock_neo4j = MagicMock()
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_neo4j.GraphDatabase.driver.return_value = mock_driver
    mock_driver.session.return_value.__enter__.return_value = mock_session
    sys.modules["neo4j"] = mock_neo4j

    pipeline = LoaderPipeline()

    payload = [
        {"id": "u1", "label": "User", "name": "Alice"},
        {"id": "u2", "label": "User", "name": "Bob"},
        {"id": "u1", "links": [{"target": "u2", "type": "KNOWS"}]},
    ]

    try:
        pipeline.run(
            input_data=payload,
            destination="neo4j://localhost:7687",
            strategy="neo4j",
            user="neo4j",
            password="password",
            id_key="id",
        )

        if mock_session.execute_write.called:
            print("✅ Mock Test Passed: Transaction executed.")
            print(
                f"   [Calls]: {mock_session.execute_write.call_count} (Nodes + Edges)"
            )
        else:
            print("❌ Mock Test Failed.")

    except Exception as e:
        print(f"❌ Mock Error: {e}")


def run_real_test():
    print("\n>>> 🕸️ [Real] Testing Pipeline -> Neo4j...")

    pipeline = LoaderPipeline()

    payload = [
        {"id": "r1", "label": "Demo", "name": "Real Node 1"},
        {"id": "r2", "label": "Demo", "name": "Real Node 2"},
        {"id": "r1", "links": [{"target": "r2", "type": "LINKED_TO"}]},
    ]

    try:
        pipeline.run(
            input_data=payload,
            destination="neo4j://localhost:7687",
            strategy="neo4j",
            user="neo4j",
            password="password",
        )
        print("✅ Real Test Passed: Check Neo4j Browser.")
    except Exception as e:
        print(f"⚠️ Real Test Skipped/Failed: {e}")


if __name__ == "__main__":
    run_mock_test()
    # run_real_test()
