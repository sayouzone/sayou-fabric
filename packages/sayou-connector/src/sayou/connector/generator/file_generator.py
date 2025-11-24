import os
import fnmatch
from typing import Iterator, List, Optional

from ..core.models import FetchTask
from ..interfaces.base_generator import BaseGenerator

class FileGenerator(BaseGenerator):
    """
    (Tier 2) 로컬 파일 시스템을 탐색하여 수집 대상을 선정하는 Generator.
    """
    component_name = "FileGenerator"
    SUPPORTED_TYPES = ["local_scan"]

    def initialize(
        self, 
        source: str, 
        recursive: bool = True, 
        extensions: Optional[List[str]] = None, 
        name_pattern: str = "*",
        **kwargs
    ):
        """
        Args:
            root_path: 탐색 시작 경로
            recursive: 하위 폴더 포함 여부
            extensions: 허용할 확장자 리스트 (예: ['.pdf', '.docx']). None이면 모두 허용.
            name_pattern: 파일명 패턴 (예: '*report*'). 기본값 '*'.
        """
        self.root_path = os.path.abspath(source)
        self.recursive = recursive
        self.extensions = [ext.lower() for ext in extensions] if extensions else None
        self.name_pattern = name_pattern

    def generate(self) -> Iterator[FetchTask]:
        """조건에 맞는 파일만 Task로 생성하여 Yield"""
        self._log(f"Scanning '{self.root_path}' (Recursive={self.recursive}, Ext={self.extensions})")

        if os.path.isfile(self.root_path):
            if self._is_valid(self.root_path):
                yield self._create_task(self.root_path)
            return

        if self.recursive:
            for root, _, files in os.walk(self.root_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    if self._is_valid(file):
                        yield self._create_task(full_path)
        else:
            # Non-recursive (현재 폴더만)
            try:
                for item in os.listdir(self.root_path):
                    full_path = os.path.join(self.root_path, item)
                    if os.path.isfile(full_path) and self._is_valid(item):
                        yield self._create_task(full_path)
            except FileNotFoundError:
                self._log(f"Path not found: {self.root_path}", level="error")

    def _is_valid(self, filename: str) -> bool:
        """필터링 로직"""
        # 1. 이름 패턴 확인 (Wildcard match)
        if not fnmatch.fnmatch(filename, self.name_pattern):
            return False
        
        # 2. 확장자 확인
        if self.extensions:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in self.extensions:
                return False
        
        return True

    def _create_task(self, path: str) -> FetchTask:
        return FetchTask(
            source_type="file", # Fetcher 라우팅 키
            uri=path,
            meta={"filename": os.path.basename(path)}
        )