from abc import abstractmethod

from sayou.core.base_component import BaseComponent

from ..core.context import RefineryContext
from ..core.exceptions import RefineryError

class BaseProcessor(BaseComponent):
    """
    (Tier 1) RefineryContext를 받아 'DataAtom' 리스트를
    처리하는 모든 프로세서의 인터페이스.
    (e.g., Deduplicator, Imputer, Aggregator)
    """
    component_name = "BaseProcessor"

    def process(self, context: RefineryContext) -> RefineryContext:
        """
        [공통 뼈대] 모든 Tier 2/3 Atom 프로세서의 진입점.
        로깅, 에러 핸들링, 실제 처리를 담당합니다.
        """
        self._log(f"Processing context with {len(context.atoms)} atoms...")
        
        try:
            # Tier 2/3가 실제 로직을 구현
            processed_context = self._do_process(context)
            
            if not isinstance(processed_context, RefineryContext):
                raise RefineryError(f"{self.component_name} did not return a valid RefineryContext.")

            self._log(f"Processing complete. Result: {len(processed_context.atoms)} atoms.")
            return processed_context

        except Exception as e:
            self._log(f"Processing failed: {e}", level="error")
            raise RefineryError(f"Failed during {self.component_name}: {e}")

    @abstractmethod
    def _do_process(self, context: RefineryContext) -> RefineryContext:
        """
        [구현 필수] 실제 Atom 처리 로직.
        
        Tier 2(Template) 또는 Tier 3(Plugin)가 이 메서드를 구현합니다.
        
        :param context: 원본 실행 컨텍스트 (DataAtom 리스트 포함)
        :return: 수정된 실행 컨텍스트
        """
        raise NotImplementedError