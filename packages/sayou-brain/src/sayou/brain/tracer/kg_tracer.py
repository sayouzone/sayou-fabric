from typing import Dict, Any

from sayou.extractor.pipeline import ExtractorPipeline

from ..interfaces.base_tracer import BaseTracer

class SayouKGTracer(BaseTracer):
    """
    (T2) sayou-extractor를 사용해 KG에서 데이터 위치를 추적.
    '도구'를 생성자에서 직접 주입받습니다.
    """
    component_name = "SayouKGTracer"

    def __init__(self, extractor_pipeline: ExtractorPipeline):
        """
        Args:
            extractor_pipeline (ExtractorPipeline): 
                KG를 쿼리하는 데 사용할 sayou-extractor의 인스턴스.
        """
        self.extractor = extractor_pipeline
        self._log("SayouKGTracer (Default) initialized.")
    
    def _do_trace(self, route_result: Dict[str, Any]) -> Dict[str, Any]:
        domain = route_result.get("domain", "general_knowledge")
        try:
            query = {
                "type": "sql", # (KG가 SQL DB라고 가정)
                "statement": "SELECT * FROM domain_kg WHERE domain = :d LIMIT 1",
                "params": {"d": domain}
            }
            # ⭐️ 주입받은 도구(Extractor) 사용
            kg_results = self.extractor.query(query)
            
            if not kg_results:
                return {"source_type": "default_vector_index"} # (기본값)
            return kg_results[0]
        except Exception as e:
            self._log(f"KG Tracing failed, falling back to default: {e}")
            return {"source_type": "default_vector_index"}