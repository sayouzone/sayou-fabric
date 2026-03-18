from collections import defaultdict
from typing import Any, Dict, List

from sayou.core.registry import register_component

from ..core.exceptions import WriterError
from ..interfaces.base_writer import BaseWriter

try:
    from neo4j import GraphDatabase
except ImportError:
    raise ImportError(
        "Neo4jWriter requires 'neo4j'. Install with 'pip install sayou-loader[neo4j]'"
    )


@register_component("writer")
class Neo4jWriter(BaseWriter):
    """
    Neo4j Writer (Graph Loader).

    Features:
    - Automatically groups nodes by 'label' for batch processing.
    - Uses 'UNWIND' + 'MERGE' for high-performance UPSERT.
    - Handles both Node creation and Relationship linking.
    """

    component_name = "Neo4jWriter"
    SUPPORTED_TYPES = ["neo4j", "graphdb", "cypher"]

    @classmethod
    def can_handle(
        cls, input_data: Any, destination: str, strategy: str = "auto"
    ) -> float:
        """
        Determines eligibility based on destination format (ext) or connection string.
        """
        if GraphDatabase is None:
            return 0.0

        if strategy in cls.SUPPORTED_TYPES:
            return 1.0

        if strategy == "auto" and destination:
            if destination.startswith("bolt://") or destination.startswith("neo4j://"):
                return 1.0

        return 0.0

    def _do_write(self, input_data: Any, destination: str, **kwargs) -> bool:
        if not GraphDatabase:
            raise WriterError("Please install 'neo4j' package (pip install neo4j).")

        # 1. Configuration parsing
        # destination: neo4j://host:7687
        uri = destination if "://" in destination else kwargs.get("uri")
        auth = kwargs.get("auth")  # (user, password) tuple
        if not auth and "user" in kwargs and "password" in kwargs:
            auth = (kwargs["user"], kwargs["password"])

        # Primary Key to use (default: 'id')
        id_key = kwargs.get("id_key", "id")

        # 2. Data normalization and grouping
        nodes = self._normalize_input_data(input_data)
        if not nodes:
            return True

        # Group nodes by label (required for batch processing)
        grouped_nodes = defaultdict(list)
        relationships = []

        for node in nodes:
            # Label extraction (default: 'Entity')
            label = node.get("label", "Entity")

            # Property sanitization (Neo4j doesn't support nested Dict -> JSON String conversion)
            props = self._sanitize_props(node)

            # ID confirmation (required)
            if id_key not in props:
                self._log(
                    f"Skipping node without ID key '{id_key}': {props}", level="warning"
                )
                continue

            grouped_nodes[label].append(props)

            # Relationship data extraction (e.g: 'links': [{'target': 'doc_2', 'type': 'WROTE'}])
            if "links" in node and isinstance(node["links"], list):
                src_id = props[id_key]
                for link in node["links"]:
                    target_id = link.get("target")
                    rel_type = link.get("type", "RELATED_TO")
                    if target_id:
                        relationships.append(
                            {"src": src_id, "tgt": target_id, "type": rel_type}
                        )

        # 3. Neo4j execution
        driver = GraphDatabase.driver(uri, auth=auth)
        try:
            with driver.session() as session:
                # A. Node loading (batch processing by label)
                for label, batch_data in grouped_nodes.items():
                    self._log(
                        f"Merging {len(batch_data)} nodes with label ':{label}'..."
                    )
                    session.execute_write(
                        self._batch_merge_nodes, label, batch_data, id_key
                    )

                # B. Relationship loading (edge connection)
                if relationships:
                    self._log(f"Creating {len(relationships)} relationships...")
                    # Group relationships by type for faster processing
                    self._process_relationships(session, relationships, id_key)

            return True
        finally:
            driver.close()

    def _batch_merge_nodes(self, tx, label, batch_data, id_key):
        """
        Cypher UNWIND to perform high-speed merge
        """
        query = f"""
        UNWIND $batch AS row
        MERGE (n:`{label}` {{ `{id_key}`: row.`{id_key}` }})
        SET n += row
        """
        tx.run(query, batch=batch_data)

    def _process_relationships(self, session, all_rels, id_key):
        """Group relationships by type"""
        rels_by_type = defaultdict(list)
        for rel in all_rels:
            rels_by_type[rel["type"]].append(rel)

        for rel_type, batch in rels_by_type.items():
            session.execute_write(self._batch_merge_rels, rel_type, batch, id_key)

    def _batch_merge_rels(self, tx, rel_type, batch, id_key):
        """
        Find two nodes and create relationship. (Don't create if nodes don't exist -> MATCH)
        """
        query = f"""
        UNWIND $batch AS rel
        MATCH (a {{ `{id_key}`: rel.src }})
        MATCH (b {{ `{id_key}`: rel.tgt }})
        MERGE (a)-[r:`{rel_type}`]->(b)
        """
        tx.run(query, batch=batch)

    def _normalize_input_data(self, input_data: Any) -> List[Dict]:
        """SayouNode(attributes/metadata) -> Dict conversion"""
        if hasattr(input_data, "nodes"):
            raw_nodes = input_data.nodes
        elif isinstance(input_data, list):
            raw_nodes = input_data
        else:
            raw_nodes = [input_data]

        normalized = []
        for n in raw_nodes:
            # SayouNode processing logic
            # attributes to default, metadata to merge
            if hasattr(n, "attributes") or hasattr(n, "metadata"):
                # 1. attributes to default
                d = getattr(n, "attributes", {}).copy()

                # 2. metadata to merge
                if hasattr(n, "metadata") and n.metadata:
                    d.update(n.metadata)

                # 3. id field correction (node_id -> id)
                if hasattr(n, "node_id") and n.node_id:
                    d["id"] = n.node_id

                # 4. content field processing
                if hasattr(n, "content") and n.content:
                    d["content"] = n.content

                normalized.append(d)

            elif isinstance(n, dict):
                normalized.append(n)

        return normalized

    def _sanitize_props(self, props: Dict) -> Dict:
        """Neo4j Property Type Restrictions (Primitive or List of Primitive)"""
        new_props = {}
        for k, v in props.items():
            if k == "links":
                continue

            if isinstance(v, (dict, list)):
                try:
                    if isinstance(v, list) and all(
                        isinstance(x, (str, int, float)) for x in v
                    ):
                        new_props[k] = v
                    else:
                        new_props[k] = json.dumps(v)
                except:
                    new_props[k] = str(v)
            else:
                new_props[k] = v
        return new_props
