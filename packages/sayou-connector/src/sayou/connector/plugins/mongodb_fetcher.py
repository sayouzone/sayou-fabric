import datetime
from typing import Any, Dict, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher

try:
    import pymongo
    from bson import ObjectId

except ImportError:
    pymongo = None
    ObjectId = None

if ObjectId is None or not isinstance(ObjectId, type):

    class ObjectId:
        pass


@register_component("fetcher")
class MongoDBFetcher(BaseFetcher):
    """
    MongoDB Fetcher.
    Handles ObjectId serialization automatically.
    """

    component_name = "MongoDBFetcher"
    SUPPORTED_TYPES = ["mongodb"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if "mongo" in uri.lower() else 0.0

    def _do_fetch(self, task: SayouTask) -> List[Dict[str, Any]]:
        if not pymongo:
            raise ImportError("Please install 'pymongo'.")

        params = task.params
        conn_args = params.get("connection_args", {})
        target_col = params.get("target")
        query_filter = params.get("query") or {}

        # Connection (Recommended URI Mode)
        # e.g: mongodb://user:pass@host:27017/dbname
        uri = conn_args.get("uri") or self._build_uri(conn_args)
        client = pymongo.MongoClient(uri)

        db_name = conn_args.get("dbname") or conn_args.get("database")
        if not db_name:
            db = client.get_default_database()
        else:
            db = client[db_name]

        try:
            collection = db[target_col]

            self._log(f"Fetching from '{target_col}' with filter: {query_filter}")

            cursor = collection.find(query_filter).limit(5000)

            results = []
            for doc in cursor:
                results.append(self._sanitize(doc))

            return results

        finally:
            client.close()

    def _build_uri(self, args):
        cred = f"{args['user']}:{args['password']}@" if args.get("user") else ""
        return f"mongodb://{cred}{args['host']}:{args.get('port', 27017)}/"

    def _sanitize(self, doc: Any) -> Any:
        """Recursively convert ObjectId and datetime to string."""
        if isinstance(doc, dict):
            return {k: self._sanitize(v) for k, v in doc.items()}
        elif isinstance(doc, list):
            return [self._sanitize(v) for v in doc]
        elif isinstance(doc, ObjectId):
            return str(doc)
        elif isinstance(doc, datetime.datetime):
            return doc.isoformat()
        return doc
