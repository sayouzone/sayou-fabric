import json
import os
import pickle
from typing import Any

from ..interfaces.base_writer import BaseWriter

class FileWriter(BaseWriter):
    """(Tier 2) 로컬 파일 시스템 저장 템플릿"""
    component_name = "FileWriter"
    SUPPORTED_TYPES = ["file", "local"]

    def _do_write(self, data: Any, destination: str, **kwargs) -> bool:
        # 1. 만약 destination이 기존에 존재하는 '폴더'라면?
        if os.path.isdir(destination):
            # 기본 파일명을 붙여줌
            destination = os.path.join(destination, "output.json")
            self._log(f"Destination is a directory. Appended filename: {destination}")

        # 2. 디렉토리 생성 (파일의 상위 폴더가 없으면 생성)
        folder = os.path.dirname(destination)
        if folder:
            os.makedirs(folder, exist_ok=True)

        # 데이터 타입별 저장 로직
        if isinstance(data, (dict, list)):
            content = json.dumps(data, indent=2, ensure_ascii=False)
            mode = "w"
            encoding = "utf-8"
        elif isinstance(data, str):
            content = data
            mode = "w"
            encoding = "utf-8"
        elif isinstance(data, bytes):
            content = data
            mode = "wb"
            encoding = None
        else:
            # Fallback: Pickle
            with open(destination + ".pkl", "wb") as f:
                pickle.dump(data, f)
            return True

        # 파일 쓰기
        with open(destination, mode, encoding=encoding) as f:
            f.write(content)
            
        return True