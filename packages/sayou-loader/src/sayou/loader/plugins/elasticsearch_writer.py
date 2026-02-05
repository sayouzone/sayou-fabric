from typing import Any, Dict, Iterator, List

from sayou.core.registry import register_component

from ..interfaces.base_writer import BaseWriter

try:
    from elasticsearch import Elasticsearch, helpers
except ImportError:
    Elasticsearch = None


@register_component("writer")
class ElasticsearchWriter(BaseWriter):
    """
    Elasticsearch Writer.

    Features:
    - Uses Bulk API for high-performance indexing.
    - Supports ID-based Upsert (idempotency).
    - Auto-creates index if not exists (Dynamic Mapping).
    """

    component_name = "ElasticsearchWriter"
    SUPPORTED_TYPES = ["elasticsearch"]

    @classmethod
    def can_handle(
        cls, input_data: Any, destination: str, strategy: str = "auto"
    ) -> float:
        if strategy in cls.SUPPORTED_TYPES:
            return 1.0
        if destination and destination.startswith("elasticsearch://"):
            return 1.0
        return 0.0

    def _do_write(self, input_data: Any, destination: str, **kwargs) -> bool:
        if not Elasticsearch:
            raise ImportError(
                "Please install 'elasticsearch' package (pip install elasticsearch)."
            )

        # 1. Configuration parsing
        # destination: http://localhost:9200/my_index (URL + Index)
        # kwargs: index_name, hosts
        index_name = kwargs.get("index_name")
        hosts = kwargs.get("hosts")

        # destination string parsing (simple logic)
        if "://" in destination:
            # ex: http://localhost:9200/target_index
            base_url, idx = destination.rsplit("/", 1)
            if not hosts:
                hosts = base_url
            if not index_name:
                index_name = idx

        if not index_name:
            raise ValueError("[ElasticsearchWriter] 'index_name' is required.")

        auth = kwargs.get("auth")  # (user, password) tuple or api_key

        # 2. Data normalization
        nodes = self._normalize_input_data(input_data)
        if not nodes:
            return True

        # 3. Client connection
        es_client = Elasticsearch(
            hosts=hosts,
            basic_auth=auth if isinstance(auth, tuple) else None,
            api_key=auth if isinstance(auth, str) else None,
            verify_certs=kwargs.get("verify_certs", True),
        )

        try:
            # Connection check
            if not es_client.ping():
                self._log(f"Cannot connect to Elasticsearch at {hosts}", level="error")
                return False

            # 4. Bulk Data (Generator)
            actions = self._generate_bulk_actions(
                nodes, index_name, kwargs.get("id_key", "id")
            )

            # 5. Execute Bulk
            self._log(f"Bulk indexing {len(nodes)} documents into '{index_name}'...")
            success, failed = helpers.bulk(es_client, actions, stats_only=True)

            self._log(f"Indexed {success} documents. (Failed: {failed})")
            if failed > 0:
                self._log(
                    f"Warning: {failed} documents failed to index.", level="warning"
                )

            return True

        finally:
            es_client.close()

    def _generate_bulk_actions(
        self, nodes: List[Dict], index_name: str, id_key: str
    ) -> Iterator[Dict]:
        """
        Elasticsearch Bulk API format conversion.
        { "_index": "name", "_id": "123", "_source": { ... } }
        """
        for node in nodes:
            action = {"_index": index_name, "_source": node}
            doc_id = node.get(id_key) or node.get("node_id") or node.get("_id")
            if doc_id:
                action["_id"] = str(doc_id)

            yield action

    def _normalize_input_data(self, input_data: Any) -> List[Dict]:
        """SayouNode -> Dict (attributes + metadata)"""
        if hasattr(input_data, "nodes"):
            raw = input_data.nodes
        elif isinstance(input_data, list):
            raw = input_data
        else:
            raw = [input_data]

        normalized = []
        for n in raw:
            if hasattr(n, "attributes") or hasattr(n, "metadata"):
                d = getattr(n, "attributes", {}).copy()

                if hasattr(n, "metadata") and n.metadata:
                    d.update(n.metadata)

                if hasattr(n, "node_id") and n.node_id:
                    d["node_id"] = n.node_id

                if hasattr(n, "content") and n.content:
                    d["content"] = n.content

                normalized.append(d)

            elif isinstance(n, dict):
                normalized.append(n)
        return normalized
