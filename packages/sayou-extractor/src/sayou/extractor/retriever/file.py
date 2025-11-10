from typing import Any, Dict, List
from ..core.exceptions import RetrievalError, QueryError
from ..interfaces.base_retriever import BaseRetriever
import os

class FileRetriever(BaseRetriever):
    """
    (Tier 2) 'file_read' 쿼리 타입에 응답하여
    로컬 파일 시스템의 텍스트를 읽어옵니다.
    """
    component_name = "FileRetriever"
    SUPPORTED_TYPES: List[str] = ["file_read"]

    def initialize(self, **kwargs):
        super().initialize(**kwargs)
        self.base_dir = kwargs.get("base_dir")
        if not self.base_dir:
            self._log("Warning: FileRetriever initialized without 'base_dir'.")

    def _do_retrieve(self, request: Dict[str, Any]) -> Any:
        """'file_read' 쿼리 요청을 실제로 처리합니다."""
        filepath_relative = request.get("filepath")
        
        if not filepath_relative:
            raise QueryError("FileRetriever request requires 'filepath'.")
        if not self.base_dir:
            raise QueryError("FileRetriever was not initialized with 'base_dir'.")
            
        full_path = os.path.join(self.base_dir, filepath_relative)
        
        self._log(f"Retrieving file: {full_path}")
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            self._log(f"Failed to read file {full_path}: {e}")
            return None