import json
import os
from typing import Any
from sayou.assembler.interfaces.base_storer import BaseStorer
from sayou.assembler.core.exceptions import StoreError
from sayou.assembler.utils.graph_model import KnowledgeGraph

class FileStorer(BaseStorer):
    """
    (Tier 2) '파일' 저장 엔진.
    구축된 객체를 JSON (KG) 또는 JSONL (Vector) 파일로 저장합니다.
    (구 store/json_store.py)
    """
    component_name = "FileStorer"

    def initialize(self, **kwargs):
        """kwargs에서 'filepath'를 받아 저장 경로를 설정합니다."""
        self.filepath = kwargs.get("filepath")
        if not self.filepath:
            raise StoreError(f"[{self.component_name}] 'filepath' is required for initialization.")
        self._log(f"FileStorer initialized. Target file: {self.filepath}")

    def store(self, built_object: Any):
        """Builder가 만든 객체 타입에 따라 분기하여 파일로 저장합니다."""
        try:
            os.makedirs(os.path.dirname(self.filepath) or ".", exist_ok=True)

            if isinstance(built_object, KnowledgeGraph):
                # 1. KG 객체는 JSON으로 저장
                self._log(f"Storing KnowledgeGraph ({len(built_object)} entities) to JSON...")
                with open(self.filepath, "w", encoding="utf-8") as f:
                    json.dump({"entities": built_object.entities}, f, ensure_ascii=False, indent=2)
            
            elif isinstance(built_object, list):
                # 2. Vector (Atom 리스트)는 JSONL로 저장 (가정)
                self._log(f"Storing VectorIndex ({len(built_object)} items) to JSONL...")
                with open(self.filepath, "w", encoding="utf-8") as f:
                    for item in built_object:
                        # (실제로는 item이 Atom이거나, (vector, metadata) 튜플일 것)
                        # 👇 [오류 수정] item이 to_dict 메서드를 가졌는지 확인
                        if hasattr(item, 'to_dict') and callable(item.to_dict):
                            f.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")
                        else:
                            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            else:
                raise StoreError(f"Unsupported object type for FileStorer: {type(built_object)}")
            
            self._log(f"Successfully stored object to {self.filepath}")

        except Exception as e:
            raise StoreError(f"Failed to store object to {self.filepath}: {e}")