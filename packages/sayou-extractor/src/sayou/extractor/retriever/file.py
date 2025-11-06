from typing import Any, Dict
from sayou.extractor.interfaces.base_retriever import BaseRetriever
from sayou.extractor.core.exceptions import RetrievalError, ExtractorError
import os

class FileRetriever(BaseRetriever):
    """(Tier 2) '로컬 파일 시스템'에서 파일 읽기 (Key-Value 조회)"""
    component_name = "FileRetriever"
    SUPPORTED_TYPES = ["file_read"] # 👈 "file_read" 처리

    def initialize(self, **kwargs):
        self.base_dir = kwargs.get("base_dir", os.getcwd())
        self.encoding = kwargs.get("encoding", "utf-8")

    def _do_retrieve(self, request: Dict[str, Any]) -> str:
        """[Tier 1 구현] 파일 읽기"""
        filepath = request.get("filepath")
        if not filepath:
            raise RetrievalError("'file_read' request requires 'filepath'.")
        
        safe_path = os.path.abspath(os.path.join(self.base_dir, filepath))
        if not safe_path.startswith(os.path.abspath(self.base_dir)):
            raise RetrievalError("File path is outside the allowed base directory.")
        
        try:
            with open(safe_path, "r", encoding=self.encoding) as f:
                return f.read()
        except FileNotFoundError:
            raise RetrievalError(f"File not found: {safe_path}")