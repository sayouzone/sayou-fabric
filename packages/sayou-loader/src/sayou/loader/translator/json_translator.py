from typing import Any
from sayou.loader.interfaces.base_translator import BaseTranslator
from sayou.core.atom import DataAtom

# (Assembler의 'utils'에 있는 KnowledgeGraph 모델을 import한다고 가정)
from sayou.assembler.utils.graph_model import KnowledgeGraph 

class JsonTranslator(BaseTranslator):
    """
    (Tier 2) 'DataAtom' 또는 'KnowledgeGraph' 객체를
    'JSON 직렬화 가능한 dict'로 변환하는 일반 엔진.
    """
    component_name = "JsonTranslator"

    def _do_translate(self, input_object: Any) -> Any:
        """[Tier 1 구현] 객체 타입에 따라 dict로 변환"""
        
        if isinstance(input_object, KnowledgeGraph):
            # Assembler의 KG 객체를 dict로 변환
            return {"entities": input_object.entities}
        
        if isinstance(input_object, list) and all(isinstance(x, DataAtom) for x in input_object):
            # Refinery의 DataAtom 리스트를 dict 리스트로 변환
            return [atom.to_dict() for atom in input_object]
        
        # (기타 객체 타입 지원...)
        
        from ..core.exceptions import TranslationError
        raise TranslationError(f"JsonTranslator does not support object type: {type(input_object)}")