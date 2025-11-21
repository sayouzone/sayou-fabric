from typing import List

from sayou.core.base_component import BaseComponent
from sayou.core.atom import DataAtom

from ..core.exceptions import SchemaError

class SchemaValidator(BaseComponent):
    """DataAtom이 온톨로지 스키마에 맞는지 검증하는 유틸리티 클래스."""
    component_name = "SchemaValidator"

    def __init__(self):
        self.ontology = None
        self.classes = {}

    def initialize(self, **kwargs):
        """kwargs에서 'ontology' 데이터를 받아 설정합니다."""
        ontology_data = kwargs.get("ontology")
        if not isinstance(ontology_data, dict):
            raise SchemaError(f"[{self.component_name}] 'ontology' dict is required for initialization.")
        self.ontology = ontology_data
        self.classes = self.ontology.get("classes", {})
        self._log("Validator initialized with ontology data.")

    def validate_atom(self, atom: DataAtom) -> bool:
        """단일 Atom의 스키마 적합성 검증"""
        if not self.ontology:
            self._log("🚨 Validator is not initialized. Skipping validation.")
            return False
            
        payload = atom.payload
        eclass = payload.get("entity_class")
        
        if not eclass:
            self._log(f"🚨 Atom {atom.atom_id} has no 'entity_class'. Invalid.")
            return False

        if eclass not in self.classes:
            self._log(f"🚨 Atom {atom.atom_id}: Unknown class '{eclass}'. Invalid.")
            return False
        
        # TODO: 필요시 predicate, attributes 검증 로직 추가
        return True

    def validate_batch(self, atoms: List[DataAtom]) -> List[DataAtom]:
        """유효한 Atom 리스트만 필터링하여 반환합니다."""
        valid_atoms = []
        for atom in atoms:
            if self.validate_atom(atom):
                valid_atoms.append(atom)
        return valid_atoms