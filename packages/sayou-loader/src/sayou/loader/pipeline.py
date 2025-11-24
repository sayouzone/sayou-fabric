from typing import Any, Dict, List, Optional

from sayou.core.base_component import BaseComponent

from .interfaces.base_writer import BaseWriter
from .writer.file_writer import FileWriter
# from .plugins.neo4j_writer import Neo4jWriter

class LoaderPipeline(BaseComponent):
    """
    (Orchestrator) 데이터를 적절한 저장소로 보냅니다.
    적절한 로더를 찾지 못하면 로컬 파일로 저장하는 안전장치(Fallback)를 가집니다.
    """
    component_name = "LoaderPipeline"

    def __init__(self, extra_writers: Optional[List[BaseWriter]] = None):
        self.handler_map: Dict[str, BaseWriter] = {}
        
        default_writers = [
            FileWriter(),
            # Neo4jWriter()
        ]
        
        self._register(default_writers)
        if extra_writers:
            self._register(extra_writers)

    def _register(self, writers: List[BaseWriter]):
        for writer in writers:
            for t in getattr(writer, "SUPPORTED_TYPES", []):
                self.handler_map[t] = writer

    def initialize(self, **kwargs):
        for handler in set(self.handler_map.values()):
            handler.initialize(**kwargs)

    def run(
        self, 
        data: Any, 
        destination: str, 
        target_type: str = "file", 
        **kwargs
    ) -> bool:
        """
        Args:
            target_type: 저장소 타입 ('neo4j', 'file' 등).
        """
        handler = self.handler_map.get(target_type)
        
        if not handler:
            self._log(f"No writer found for '{target_type}'. Fallback to 'file'.", level="warning")
            handler = self.handler_map.get("file")
            
            if "://" in destination: 
                destination = "fallback_dump.json"
                self._log(f"Destination changed to local file: {destination}")

        self._log(f"Loading data using {handler.component_name}...")
        
        try:
            return handler.write(data, destination, **kwargs)
        except Exception as e:
            self._log(f"Pipeline Error: {e}")
            return False