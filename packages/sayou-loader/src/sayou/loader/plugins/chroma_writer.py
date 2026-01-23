import json
from typing import Any, Dict, List, Tuple

from sayou.core.registry import register_component

from ..interfaces.base_writer import BaseWriter

try:
    import chromadb
except ImportError:
    chromadb = None


@register_component("writer")
class ChromaWriter(BaseWriter):
    """
    (Tier 2) Writes SayouNodes to ChromaDB.
    Supports both PersistentClient (Local) and HttpClient (Server).

    URI Pattern: chroma://<path_or_host>/<collection_name>
    """

    component_name = "ChromaWriter"
    SUPPORTED_TYPES = ["chroma", "chromadb"]

    @classmethod
    def can_handle(
        cls, input_data: Any, destination: str, strategy: str = "auto"
    ) -> float:
        if strategy in cls.SUPPORTED_TYPES:
            return 1.0
        if destination and destination.startswith("chroma://"):
            return 1.0
        return 0.0

    def _do_write(self, input_data: Any, destination: str, **kwargs) -> bool:
        if not chromadb:
            self._log("Package 'chromadb' is required.", level="error")
            return False

        # 1. Destination Parse & Client Init
        path, collection_name = self._parse_destination(destination)

        try:
            client = self._get_client(path, **kwargs)
            collection = client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": kwargs.get("distance_func", "cosine")},
            )
        except Exception as e:
            self._log(f"Chroma Init Error: {e}", level="error")
            return False

        # 2. Data normalization (Standard Pattern)
        nodes = self._normalize_input_data(input_data)
        if not nodes:
            self._log("No nodes to insert.", level="warning")
            return True

        # 3. Chroma Data Structure Conversion
        ids, docs, metas, embeddings = [], [], [], []

        for i, node in enumerate(nodes):
            n_id = str(node.get("id") or node.get("node_id") or f"node_{i}")

            text = (
                node.get("content") or node.get("text") or node.get("schema:text") or ""
            )

            vector = node.get("vector")

            exclude = {
                "id",
                "node_id",
                "content",
                "text",
                "schema:text",
                "vector",
                "vector_dim",
            }
            raw_meta = {k: v for k, v in node.items() if k not in exclude}
            clean_meta = self._sanitize_metadata(raw_meta)

            ids.append(n_id)
            docs.append(str(text))
            metas.append(clean_meta)

            if vector:
                embeddings.append(vector)

        # 4. Upsert Execution
        try:
            if embeddings and len(embeddings) == len(ids):
                collection.upsert(
                    ids=ids,
                    documents=docs,
                    metadatas=metas,
                    embeddings=embeddings,
                )
                self._log(
                    f"✅ Upserted {len(ids)} items (with vectors) to '{collection_name}'"
                )
            else:
                self._log(
                    "⚠️ Some vectors missing. Using Chroma's default embedding.",
                    level="warning",
                )
                collection.upsert(
                    ids=ids,
                    documents=docs,
                    metadatas=metas,
                )
                self._log(
                    f"✅ Upserted {len(ids)} items (auto-embedded) to '{collection_name}'"
                )

            return True

        except Exception as e:
            self._log(f"Chroma Write Error: {e}", level="error")
            return False

    # --- Helpers ---

    def _normalize_input_data(self, input_data: Any) -> List[Dict]:
        """[Standard] SayouNode -> Dict Conversion (attributes + metadata merged)"""
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
                    d["id"] = n.node_id
                if hasattr(n, "content") and n.content:
                    d["content"] = n.content
                if hasattr(n, "vector") and n.vector:
                    d["vector"] = n.vector

                normalized.append(d)
            elif isinstance(n, dict):
                normalized.append(n)
        return normalized

    def _sanitize_metadata(self, metadata: Dict) -> Dict:
        """ChromaDB only allows str, int, float, bool, so complex objects are stringified into JSON"""
        clean = {}
        for k, v in metadata.items():
            if v is None:
                continue
            if isinstance(v, (str, int, float, bool)):
                clean[k] = v
            else:
                try:
                    clean[k] = json.dumps(v, ensure_ascii=False)
                except:
                    clean[k] = str(v)
        return clean

    def _parse_destination(self, destination: str) -> Tuple[str, str]:
        clean = destination.replace("chroma://", "")
        if "/" in clean:
            parts = clean.rsplit("/", 1)
            return parts[0], parts[1]
        return "./chroma_db", clean

    def _get_client(self, path: str, **kwargs):
        if ":" in path and not (path.startswith(".") or path.startswith("/")):
            host, port = path.split(":")
            self._log(f"Connecting to Chroma Server: {host}:{port}")
            return chromadb.HttpClient(host=host, port=int(port))

        self._log(f"Connecting to Local Chroma: {path}")
        return chromadb.PersistentClient(path=path)
