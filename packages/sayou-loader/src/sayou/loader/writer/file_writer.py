from typing import Any, List, Dict
from sayou.loader.interfaces.base_writer import BaseWriter
from sayou.loader.core.exceptions import WriterError
import json
import os

class FileWriter(BaseWriter):
    """
    (Tier 2) '변환된 데이터'(dict, list)를 '파일'에 쓰는 일반 엔진.
    (JSON, JSONL, TXT 포맷 지원)
    """
    component_name = "FileWriter"
    
    def initialize(self, **kwargs):
        """
        'filepath'와 'format' (json, jsonl)을 주입받습니다.
        """
        self.filepath = kwargs.get("filepath")
        self.format = kwargs.get("format", "json") # 기본값 json
        
        if not self.filepath:
            raise WriterError("FileWriter requires a 'filepath'.")

    def _do_write(self, translated_data: Any):
        """[Tier 1 구현] 포맷에 따라 파일 쓰기 수행"""
        
        try:
            os.makedirs(os.path.dirname(self.filepath) or ".", exist_ok=True)
            
            with open(self.filepath, "w", encoding="utf-8") as f:
                if self.format == "json":
                    if not isinstance(translated_data, (Dict, List)):
                        raise WriterError("JSON format requires 'dict' or 'list' data.")
                    json.dump(translated_data, f, ensure_ascii=False, indent=2)
                
                elif self.format == "jsonl":
                    if not isinstance(translated_data, list):
                        raise WriterError("JSONL format requires 'list' data.")
                    for item in translated_data:
                        f.write(json.dumps(item, ensure_ascii=False) + "\n")
                
                # (기타 'txt' 등 포맷 추가 가능)
                
                else:
                    raise WriterError(f"Unsupported format: {self.format}")
        
        except (IOError, TypeError) as e:
            raise WriterError(f"Failed to write file {self.filepath}: {e}")