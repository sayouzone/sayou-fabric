from typing import Dict, Any, List, Optional

from sayou.core.base_component import BaseComponent

class SayouRAGPipeline(BaseComponent):
    """
    Core orchestration engine for Sayou RAG pipelines.
    - Acts as the foundation for both Basic and Advanced RAG.
    - Supports ordered or dependency-based stage execution.
    """

    def __init__(self):
        self.stages: Dict[str, Any] = {}
        self.execution_order: List[str] = []

    def add_stage(self, name: str, stage_obj: Any):
        """Register a new stage component."""
        self.stages[name] = stage_obj
        self.execution_order.append(name)
        return self

    def get_stage(self, name: str) -> Optional[Any]:
        return self.stages.get(name)

    def initialize_all(self, **kwargs):
        """Initialize all stages that define initialize()."""
        for name, stage in self.stages.items():
            if hasattr(stage, "initialize"):
                try:
                    stage.initialize(**kwargs)
                    self._log(f"[INIT] ✅ {name} initialized.")
                except Exception as e:
                    self._log(f"[INIT] ⚠️ {name} init failed: {e}")
        return self

    def run(self, **kwargs) -> Any:
        """
        Sequentially execute stages.
        """
        self._log("[RAG] 🚀 Starting pipeline run...")
        data = kwargs

        for name in self.execution_order:
            stage = self.stages[name]
            if not hasattr(stage, "run"):
                self._log(f"[RAG] ⚠️ Stage {name} has no 'run' method. Skipping.")
                continue

            self._log(f"[RAG] ▶️ Running stage: {name}")
            try:
                stage_input = data
                result = stage.run(**stage_input)

                if isinstance(result, dict):
                    data.update(result)
                else:
                    data["data"] = result

            except Exception as e:
                self._log(f"[RAG] ❌ Stage {name} failed: {e}")
                raise e # 실패 시 중단

        self._log("[RAG] ✅ Pipeline completed.")
        return data