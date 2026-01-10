# Copyright (c) 2025, Sayouzone
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class FileStorage:
    """파일 저장을 담당하는 클래스"""

    def __init__(self, base_path: str = "./downloads"):
        self._base_path = Path(base_path)

    @property
    def base_path(self) -> Path:
        return self._base_path

    def save(self, filename: str, content: bytes, subdir: str = "") -> str:
        """
        파일을 로컬에 저장합니다.
        
        Args:
            filename: 저장할 파일명
            content: 파일 내용
            subdir: 하위 디렉토리 (선택)
            
        Returns:
            저장된 파일의 전체 경로
        """
        target_dir = self._base_path / subdir if subdir else self._base_path
        target_dir.mkdir(parents=True, exist_ok=True)

        file_path = target_dir / filename

        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"파일 저장 완료: {file_path}")
        return str(file_path)

    def exists(self, filename: str, subdir: str = "") -> bool:
        """파일 존재 여부를 확인합니다."""
        target_dir = self._base_path / subdir if subdir else self._base_path
        return (target_dir / filename).exists()

    def get_path(self, filename: str, subdir: str = "") -> str:
        """파일 경로를 반환합니다."""
        target_dir = self._base_path / subdir if subdir else self._base_path
        return str(target_dir / filename)