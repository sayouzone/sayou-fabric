import copy
from typing import List

from sayou.core.atom import DataAtom

from ..core.exceptions import RefineryError
from ..interfaces.base_processor import BaseProcessor

class MissingValueImputer(BaseProcessor):
    """
    (Tier 2) 결측치(Missing Value) 처리 엔진.
    Atom payload의 필드를 지정된 값/전략으로 채웁니다.
    """
    component_name = "MissingValueImputer"

    def initialize(self, **kwargs):
        """
        'imputation_rules'를 설정합니다.
        e.g., rules = {
            "payload.price": {"strategy": "constant", "value": 0.0},
            "payload.description": {"strategy": "constant", "value": "N/A"}
        }
        """
        self.rules = kwargs.get("imputation_rules", {})
        if not self.rules:
            raise RefineryError("ImputationRules must be provided.")
        self._log(f"Initialized with {len(self.rules)} imputation rules.")

    def process(self, atoms: List[DataAtom]) -> List[DataAtom]:
        processed_atoms = []
        for atom in atoms:
            atom_copy = copy.deepcopy(atom)
            try:
                processed_atoms.append(self._apply_rules(atom_copy))
            except Exception as e:
                self._log(f"Failed to impute atom {atom.atom_id}: {e}")
        return processed_atoms

    def _apply_rules(self, atom: DataAtom) -> DataAtom:
        for field_path, rule in self.rules.items():
            # (간단한 예시: 2-depth 경로만 지원. e.g., "payload.price")
            keys = field_path.split('.')
            if len(keys) != 2 or keys[0] != 'payload':
                continue # 지금은 'payload.field'만 지원

            target_dict = atom.payload
            key = keys[1]
            
            # 값이 'None'이거나 키가 아예 존재하지 않을 때
            if target_dict.get(key) is None:
                if rule.get("strategy") == "constant":
                    target_dict[key] = rule.get("value")
                # (향후 'mean', 'median' 등 다른 전략 추가 가능)
                
        return atom