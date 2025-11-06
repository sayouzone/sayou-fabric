class KnowledgeGraph:
    """
    빌드된 엔티티들을 담는 인메모리(in-memory) 지식 그래프 표현.
    (구 graph/knowledge_graph.py)
    
    이 객체는 KG 빌더가 생성하고 Storer가 소비하는 순수 데이터 컨테이너입니다.
    """
    def __init__(self, entities: dict):
        self.entities = entities

    def get_node(self, entity_id: str):
        """특정 노드 데이터를 반환합니다."""
        return self.entities.get(entity_id)

    def __len__(self):
        """그래프 내의 총 엔티티 수를 반환합니다."""
        return len(self.entities)