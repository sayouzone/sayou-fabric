import copy
from typing import List, Dict, Any
from sayou.refinery.interfaces.base_processor import BaseProcessor
from sayou.core.atom import DataAtom
from sayou.refinery.core.exceptions import RefineryError

class OutlierHandler(BaseProcessor):
    """
    (Tier 2) 이상치(Outlier) 처리 엔진.
    규칙에 따라 Atom을 '제거(drop)'하거나 '조정(clamp)'합니다.
    """
    component_name = "OutlierHandler"

    def initialize(self, **kwargs):
        """
        'outlier_rules'를 설정합니다.
        e.g., rules = {
            "payload.price": {"min": 0, "max": 10000, "action": "clamp"},
            "payload.age": {"min": 0, "action": "drop"}
        }
        """
        self.rules = kwargs.get("outlier_rules", {})
        if not self.rules:
            raise RefineryError("OutlierRules must be provided.")
        self._log(f"Initialized with {len(self.rules)} outlier rules.")

    def process(self, atoms: List[DataAtom]) -> List[DataAtom]:
        processed_atoms = []
        for atom in atoms:
            atom_copy = copy.deepcopy(atom)
            
            if self._check_rules(atom_copy):
                # 모든 규칙을 통과했거나, 'clamp'로 조정된 경우
                processed_atoms.append(atom_copy)
            # (check_rules가 False를 반환하면 'drop'되어 리스트에 추가되지 않음)

        return processed_atoms

    def _check_rules(self, atom: DataAtom) -> bool:
        """규칙을 적용하고, Atom을 유지할지(True) 버릴지(False) 반환"""
        for field_path, rule in self.rules.items():
            keys = field_path.split('.')
            if len(keys) != 2 or keys[0] != 'payload': continue
            
            value = atom.payload.get(keys[1])
            if value is None: continue # 결측치는 이 핸들러의 소관이 아님
            
            try:
                value_f = float(value)
                action = rule.get("action", "drop") # 기본값은 'drop'

                # 최소값 위반
                if "min" in rule and value_f < rule["min"]:
                    if action == "drop": return False
                    if action == "clamp": atom.payload[keys[1]] = rule["min"]
                
                # 최대값 위반
                if "max" in rule and value_f > rule["max"]:
                    if action == "drop": return False
                    if action == "clamp": atom.payload[keys[1]] = rule["max"]
                    
            except (ValueError, TypeError):
                continue # 숫자 필드가 아니면 무시
        
        return True # 모든 규칙 통과