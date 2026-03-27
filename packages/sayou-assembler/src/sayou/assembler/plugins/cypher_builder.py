import json
from typing import Any, List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouOutput

from ..interfaces.base_builder import BaseBuilder


@register_component("builder")
class CypherBuilder(BaseBuilder):
    """
    Converts SayouNodes into Neo4j Cypher Queries.

    Generates 'MERGE' statements for nodes and relationships to ensure idempotency.
    Returns a list of query strings executable by a Neo4j driver.
    """

    component_name = "CypherBuilder"
    SUPPORTED_TYPES = ["cypher", "neo4j"]

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        if strategy in ["cypher", "neo4j"]:
            return 1.0

        return 0.0

    def _do_build(self, data: SayouOutput) -> List[str]:
        """
        Generate Cypher query strings.
        """
        queries = []

        # 1. Create Nodes (UNWIND batching is better, but simple MERGE here for clarity)
        for node in data.nodes:
            props = node.attributes.copy()
            if node.friendly_name:
                props["friendly_name"] = node.friendly_name

            # Use json.dumps to handle property value escaping.
            props_str = self._dict_to_cypher_props(props)
            label = self._clean_label(node.node_class)

            # MERGE: 없으면 생성, 있으면 매칭
            q = f"MERGE (n:`{label}` {{id: '{node.node_id}'}}) SET n += {props_str}"
            queries.append(q)

        # 2. Create Relationships
        for node in data.nodes:
            source_id = node.node_id
            for rel_type, targets in node.relationships.items():
                if isinstance(targets, str):
                    targets = [targets]

                rel_label = self._clean_label(rel_type)

                for target_id in targets:
                    q = (
                        f"MATCH (a {{id: '{source_id}'}}), (b {{id: '{target_id}'}}) "
                        f"MERGE (a)-[:`{rel_label}`]->(b)"
                    )
                    queries.append(q)

        return queries

    def _dict_to_cypher_props(self, props: dict) -> str:
        """
        Helper to convert a Python dictionary into a Cypher map string.
        """
        # json.dumps handles quoting. Neo4j accepts JSON-compatible map literals,
        # so keeping keys quoted is acceptable for simplicity.
        return json.dumps(props, ensure_ascii=False)

    def _clean_label(self, label: str) -> str:
        """
        Sanitize or format the ontology label for Cypher syntax.
        """
        return label.replace(":", "_")
