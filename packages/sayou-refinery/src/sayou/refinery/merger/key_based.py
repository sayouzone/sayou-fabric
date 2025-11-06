import copy
from abc import abstractmethod
from typing import List, Dict, Any, Tuple
from sayou.refinery.interfaces.base_merger import BaseMerger
from sayou.core.atom import DataAtom
from sayou.refinery.core.context import RefineryContext

class KeyBasedMerger(BaseMerger):
    """
    (Tier 2) '키(Key)' 기반으로 Atom과 외부 데이터를 '병합'하는
    '일반 로직' 엔진 (템플릿).
    """
    component_name = "KeyBasedMerger"

    # --- Template Method ---
    def merge(self, context: RefineryContext) -> RefineryContext:
        atoms = context.atoms
        external_data = context.external_data

        self._log(f"Merging {len(atoms)} atoms with {len(external_data)} external records.")
        merged_atoms = []
        
        for atom in atoms:
            atom_copy = copy.deepcopy(atom)
            try:
                # 1. 자식(Tier 3)이 Atom에서 '조회 키'를 추출
                lookup_key = self._get_atom_lookup_key(atom_copy)
                if lookup_key is None:
                    merged_atoms.append(atom_copy) # 병합 대상 아님
                    continue
                
                # 2. 외부 데이터에서 해당 키의 '강화 데이터'를 찾음
                data_to_merge = external_data.get(lookup_key)
                if data_to_merge is None:
                    merged_atoms.append(atom_copy) # 조회된 데이터 없음
                    continue
                    
                # 3. 자식(Tier 3)이 Atom과 강화 데이터를 '병합'
                atom_copy = self._merge_data_into_atom(atom_copy, data_to_merge)
                merged_atoms.append(atom_copy)
                
            except Exception as e:
                self._log(f"Failed to merge atom {atom.atom_id}: {e}")
                merged_atoms.append(atom_copy) # 실패 시 원본 Atom 유지
        
        context.atoms = merged_atoms
        return context

    # --- Abstract Methods (Tier 3가 구현할 부분) ---

    @abstractmethod
    def _get_atom_lookup_key(self, atom: DataAtom) -> str | None:
        """
        Tier 3(e.g., EmployeeEnricher)가 구현:
        Atom에서 외부 데이터를 조회할 '키'를 반환합니다.
        (e.g., return atom.payload.get("employee_id"))
        """
        raise NotImplementedError

    @abstractmethod
    def _merge_data_into_atom(self, atom: DataAtom, data_to_merge: Dict[str, Any]) -> DataAtom:
        """
        Tier 3(e.g., EmployeeEnricher)가 구현:
        조회된 'data_to_merge'를 'atom'의 payload에 어떻게 병합할지 정의합니다.
        (e.g., atom.payload["employee_name"] = data_to_merge.get("name"))
        """
        raise NotImplementedError