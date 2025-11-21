import json

from sayou.core.base_component import BaseComponent

from ..core.exceptions import SchemaError

class SchemaManager(BaseComponent):
    """
    온톨로지 스키마 파일을 로드하고 관리하는 유틸리티 클래스.
    (Tier 2, 3의 여러 컴포넌트가 공유)
    """
    component_name = "SchemaManager"

    def __init__(self):
        self.ontology = None

    def initialize(self, **kwargs):
        """kwargs에서 'ontology_path'를 찾아 스키마를 로드합니다."""
        filepath = kwargs.get("ontology_path")
        if not filepath:
            raise SchemaError(f"[{self.component_name}] 'ontology_path' is required for initialization.")
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if "classes" not in data or "predicates" not in data:
                raise SchemaError("Invalid ontology file structure. Missing 'classes' or 'predicates'.")
            self.ontology = data
            self._log(f"Ontology loaded successfully from {filepath}")
        except FileNotFoundError:
            raise SchemaError(f"Ontology file not found at: {filepath}")
        except json.JSONDecodeError:
            raise SchemaError(f"Failed to decode JSON from: {filepath}")

    def get_ontology(self) -> dict:
        """로드된 온톨로지 데이터를 반환합니다."""
        if not self.ontology:
            raise SchemaError("Ontology is not loaded. Please run initialize() first.")
        return self.ontology