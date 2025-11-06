from abc import abstractmethod
from typing import Any
from sayou.core.base_component import BaseComponent
from ..core.exceptions import TranslationError

class BaseTranslator(BaseComponent):
    """
    (Tier 1) 'DataAtom' 또는 'KnowledgeGraph' 객체를
    '저장소별 데이터 형식'(e.g., JSON, Cypher, SQL)으로 '변환'하는
    모든 Translator의 인터페이스. (Template Method)
    """
    component_name = "BaseTranslator"
    
    def translate(self, input_object: Any) -> Any:
        """
        [공통 골격] 변환 프로세스를 실행하고 로깅/예외처리를 수행합니다.
        Tier 2/3는 이 메서드를 오버라이드하지 않습니다.
        
        :param input_object: Assembler/Refinery가 생성한 객체
            (e.g., KnowledgeGraph, List[DataAtom])
        :return: Writer가 사용할 수 있는 변환된 데이터
            (e.g., List[dict], List[str(Cypher 쿼리)])
        """
        self._log(f"Translating object of type '{type(input_object)}'...")
        try:
            # Tier 2/3가 '알맹이'를 구현
            translated_data = self._do_translate(input_object)
            
            self._log(f"Translation complete. Output type: '{type(translated_data)}'.")
            return translated_data
        except Exception as e:
            self._log(f"Translation failed: {e}")
            raise TranslationError(f"Translation failed: {e}")

    @abstractmethod
    def _do_translate(self, input_object: Any) -> Any:
        """
        [구현 필수] 실제 변환 로직입니다.
        (e.g., KnowledgeGraph -> Cypher 쿼리 리스트 생성)
        """
        raise NotImplementedError