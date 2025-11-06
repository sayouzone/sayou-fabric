from typing import List, Any
from sayou.assembler.interfaces.base_builder import BaseBuilder
from sayou.core.atom import DataAtom

class DefaultVectorBuilder(BaseBuilder):
    """
    (Tier 2) '일반 Vector' 구축 엔진 (Placeholder).
    Atom을 받아 인메모리 인덱스(e.g., list)로 구축합니다.
    """
    component_name = "DefaultVectorBuilder"

    def build(self, atoms: List[DataAtom]) -> Any:
        self._log(f"VectorBuilder (Placeholder): 'Building' {len(atoms)} atoms...")
        # (실제 구현 시: 여기서 Atom payload를 text로 변환하고,
        #  Embedding 모델을 호출하여 vector와 metadata 리스트를 생성)
        
        # v.0.0.1 에서는 Atom 리스트를 그대로 반환 (Storer가 처리하도록)
        in_memory_index = atoms 
        return in_memory_index