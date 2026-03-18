from typing import Any, Dict, List

from sayou.core.registry import register_component

from ..interfaces.base_writer import BaseWriter

try:
    import pymongo
    from pymongo import UpdateOne
except ImportError:
    pymongo = None


@register_component("writer")
class MongoDBWriter(BaseWriter):
    """
    MongoDB Writer.

    Features:
    - Uses 'bulk_write' for high-performance batch processing.
    - Supports UPSERT based on a specific key (default: 'id').
    - Schemaless: Accepts any JSON-like structure.
    """

    component_name = "MongoDBWriter"
    SUPPORTED_TYPES = ["mongodb"]

    @classmethod
    def can_handle(
        cls, input_data: Any, destination: str, strategy: str = "auto"
    ) -> float:
        if strategy in cls.SUPPORTED_TYPES:
            return 1.0
        if destination and destination.startswith("mongodb://"):
            return 1.0
        return 0.0

    def _do_write(self, input_data: Any, destination: str, **kwargs) -> bool:
        if not pymongo:
            raise ImportError("Please install 'pymongo' package.")

        # 1. Configuration parsing
        # destination: mongodb://localhost:27017/dbname/collection
        # kwargs: collection, connection_args

        uri = destination if "://" in destination else kwargs.get("uri")
        conn_args = kwargs.get("connection_args", {})

        if not uri:
            host = conn_args.get("host", "localhost")
            port = conn_args.get("port", 27017)
            cred = (
                f"{conn_args['user']}:{conn_args['password']}@"
                if conn_args.get("user")
                else ""
            )
            uri = f"mongodb://{cred}{host}:{port}/"

        # DB name and collection name extraction
        db_name = kwargs.get("dbname") or kwargs.get("database")
        collection_name = kwargs.get("collection")

        # destination string parsing (mongodb://.../db/col)
        if "://" in destination:
            try:
                # ex: mongodb://localhost:27017/test_db/my_col
                path_parts = destination.split("?")[0].split("/")
                if len(path_parts) >= 5:
                    if not collection_name:
                        collection_name = path_parts[-1]
                    if not db_name:
                        db_name = path_parts[-2]
            except:
                pass

        if not collection_name:
            raise ValueError("[MongoDBWriter] 'collection' name is required.")

        # Upsert key (default: 'id'. fallback to '_id' etc)
        id_key = kwargs.get("id_key", "id")

        # 2. Data normalization
        nodes = self._normalize_input_data(input_data)
        if not nodes:
            return True

        # 3. MongoDB connection
        client = pymongo.MongoClient(uri)
        if not db_name:
            db = client.get_default_database()
        else:
            db = client[db_name]

        collection = db[collection_name]

        try:
            # 4. Bulk Upsert Operation creation
            operations = []
            for node in nodes:
                # Primary key value extraction
                doc_id = node.get(id_key) or node.get("_id") or node.get("node_id")

                if doc_id:
                    # ID exists: Upsert (Insert if not exists, Update if exists)
                    operations.append(
                        UpdateOne(
                            filter={id_key: doc_id}, update={"$set": node}, upsert=True
                        )
                    )
                else:
                    from pymongo import InsertOne

                    operations.append(InsertOne(node))

            # 5. Execute
            if operations:
                self._log(
                    f"Bulk writing {len(operations)} documents to '{collection_name}'..."
                )
                result = collection.bulk_write(operations)
                self._log(
                    f"Matched: {result.matched_count}, Modified: {result.modified_count}, Upserted: {result.upserted_count}, Inserted: {result.inserted_count}"
                )

            return True

        finally:
            client.close()

    def _normalize_input_data(self, input_data: Any) -> List[Dict]:
        """SayouNode -> Dict conversion (attributes + metadata merged)"""
        if hasattr(input_data, "nodes"):
            raw = input_data.nodes
        elif isinstance(input_data, list):
            raw = input_data
        else:
            raw = [input_data]

        normalized = []
        for n in raw:
            if hasattr(n, "attributes") or hasattr(n, "metadata"):
                # 1. attributes copy (if not exists, empty dict)
                d = getattr(n, "attributes", {}).copy()

                # 2. metadata merge
                if hasattr(n, "metadata") and n.metadata:
                    d.update(n.metadata)

                # 3. Required fields (node_id -> id mapping)
                if hasattr(n, "node_id") and n.node_id:
                    d["id"] = n.node_id

                # 4. Content
                if hasattr(n, "content") and n.content:
                    d["content"] = n.content

                normalized.append(d)

            elif isinstance(n, dict):
                normalized.append(n)
        return normalized
