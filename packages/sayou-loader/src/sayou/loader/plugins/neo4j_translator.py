from typing import Any, List
from sayou.loader.interfaces.base_translator import BaseTranslator
from sayou.loader.core.exceptions import TranslationError
from sayou.assembler.utils.graph_model import KnowledgeGraph

class Neo4jTranslator(BaseTranslator):
    """
    (Tier 3) 'KnowledgeGraph' 객체를 'Cypher 쿼리 리스트'로 변환하는
    특화 어댑터. (의존성 없음)
    """
    component_name = "Neo4jTranslator"

    def _do_translate(self, input_object: Any) -> List[str]:
        """[Tier 1 구현] KG -> Cypher 변환"""
        
        if not isinstance(input_object, KnowledgeGraph):
            raise TranslationError("Neo4jTranslator requires a KnowledgeGraph object.")
            
        cypher_queries = []
        
        # 1. 노드 생성 쿼리 (MERGE)
        for entity_id, node in input_object.entities.items():
            # (간단한 예시: entity_class를 Label로 사용)
            label = node.get("class", "Resource").split(":")[-1]
            # (JSON 직렬화가 아닌, Cypher 포맷으로 속성 생성)
            props = f"entity_id: '{entity_id}', friendly_name: '{node.get('friendly_name', '')}'"
            cypher_queries.append(f"MERGE (n:{label} {{entity_id: '{entity_id}'}}) SET n += {{{props}}}")
        
        # 2. 관계 생성 쿼리 (MERGE)
        for entity_id, node in input_object.entities.items():
            for predicate, targets in node.get("relationships", {}).items():
                rel_type = predicate.split(":")[-1].upper()
                for target_id in targets:
                    if target_id in input_object.entities:
                        cypher_queries.append(
                            f"MATCH (a {{entity_id: '{entity_id}'}}), (b {{entity_id: '{target_id}'}}) "
                            f"MERGE (a)-[:{rel_type}]->(b)"
                        )
                        
        return cypher_queries