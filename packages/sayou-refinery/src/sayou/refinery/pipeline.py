from typing import List, Dict, Any
from sayou.core.base_component import BaseComponent
from sayou.core.atom import DataAtom
from sayou.refinery.core.exceptions import RefineryError
from sayou.refinery.core.context import RefineryContext
from sayou.refinery.interfaces.base_processor import BaseProcessor
from sayou.refinery.interfaces.base_aggregator import BaseAggregator
from sayou.refinery.interfaces.base_merger import BaseMerger

RefinerStep = BaseProcessor | BaseAggregator| BaseMerger

class Pipeline(BaseComponent):
    """
    Refinery 파이프라인 (Orchestrator).
    모든 Refiner(Processor, Aggregator, Merger)를 '순차적'으로 실행합니다.
    """
    component_name = "RefineryPipeline"

    def __init__(self, steps: List[RefinerStep]):
        if not steps:
            raise RefineryError("Pipeline must have at least one step.")
        
        self.steps = steps
        self._log(f"Pipeline initialized with {len(steps)} steps.")

    def initialize(self, **kwargs):
        """각 단계를 초기화합니다."""
        try:
            for step in self.steps:
                step.initialize(**kwargs)
        except Exception as e:
            raise RefineryError(f"Failed to initialize pipeline step {step.component_name}: {e}")
        self._log("All steps initialized.")

    def run(self, key_atoms: List[DataAtom], key_external_data: Dict[str, Any] = None) -> List[DataAtom]:
        """
        파이프라인을 순차 실행합니다.
        
        :param atoms: 정제할 원본 DataAtom 리스트
        :param external_data: (선택적) Merger가 사용할 외부 조회 데이터
        :return: 모든 정제가 완료된 DataAtom 리스트
        """
        self._log(f"Refinery run started with {len(key_atoms)} atoms.")
        
        # 1. 파이프라인 실행 컨텍스트 생성
        context = RefineryContext(
            atoms=key_atoms,
            external_data=key_external_data or {}
        )
        
        for i, step in enumerate(self.steps):
            if not context.atoms:
                self._log(f"Step {i+1} ({step.component_name}): No atoms to process. Skipping.")
                continue

            self._log(f"[Step {i+1}/{len(self.steps)}] Running: {step.component_name}...")
            
            # 2. 모든 스텝은 동일한 'execute' 메서드를 호출 (시그니처 통일)
            if isinstance(step, BaseProcessor):
                context = step.process(context)
            elif isinstance(step, BaseAggregator):
                context = step.aggregate(context)
            elif isinstance(step, BaseMerger):
                context = step.merge(context)
            else:
                raise RefineryError(f"Unknown step type in pipeline: {type(step)}")
            
            self._log(f"Step {i+1} complete. Result: {len(context.atoms)} atoms.")

        self._log(f"Refinery run finished. Final output: {len(context.atoms)} atoms.")
        
        # 3. 최종 결과물인 Atom 리스트만 반환
        return context.atoms