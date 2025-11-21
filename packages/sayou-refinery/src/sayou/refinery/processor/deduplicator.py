from typing import List, Set

from sayou.core.atom import DataAtom

from ..interfaces.base_processor import BaseProcessor
from ..core.exceptions import RefineryError

class Deduplicator(BaseProcessor):
    """
    (Tier 2) 중복(Duplicate) 데이터 처리 엔진.
    지정된 key_field를 기준으로 중복 Atom을 제거합니다.
    """
    component_name = "Deduplicator"

    def initialize(self, **kwargs):
        """
        'key_field'를 설정합니다.
        e.g., key_field = "payload.entity_id" 또는 "atom_id"
        """
        self.key_field = kwargs.get("key_field")
        if not self.key_field:
            raise RefineryError("Deduplicator requires a 'key_field'.")
        
        self.key_path = self.key_field.split('.')
        self._log(f"Initialized to deduplicate based on: '{self.key_field}'")

    def process(self, atoms: List[DataAtom]) -> List[DataAtom]:
        self._log(f"Deduplicating {len(atoms)} atoms...")
        seen_keys: Set[str] = set()
        unique_atoms: List[DataAtom] = []

        for atom in atoms:
            try:
                key = self._get_key(atom)
                if key is None: # 키가 없는 Atom은 유지 (또는 정책에 따라 제거)
                    unique_atoms.append(atom)
                    continue

                if key not in seen_keys:
                    seen_keys.add(key)
                    unique_atoms.append(atom)
            
            except Exception as e:
                self._log(f"Skipping atom {atom.atom_id} during dedupe: {e}")
        
        self._log(f"Deduplication complete. {len(unique_atoms)} unique atoms remain.")
        return unique_atoms

    def _get_key(self, atom: DataAtom) -> str | None:
        """Atom에서 지정된 key_field의 값을 추출합니다."""
        if len(self.key_path) == 1:
            return getattr(atom, self.key_path[0], None)
        
        if len(self.key_path) == 2 and self.key_path[0] == 'payload':
            return atom.payload.get(self.key_path[1])
        
        # (향후 3-depth 이상 지원 시 로직 추가)
        raise RefineryError(f"Unsupported key_field path: {self.key_field}")