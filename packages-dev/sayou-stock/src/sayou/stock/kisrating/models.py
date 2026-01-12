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

import pandas as pd

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple

"""
Kisrating Data Models
"""

class FileType(Enum):
    """파일 유형 열거형"""
    EXCEL = auto()
    ZIP = auto()
    CSV = auto()
    UNKNOWN = auto()

    @classmethod
    def from_filename(cls, filename: str) -> "FileType":
        """파일명으로부터 파일 유형을 감지합니다."""
        lower_name = filename.lower()
        
        extension_map = {
            (".xlsx", ".xls"): cls.EXCEL,
            (".zip",): cls.ZIP,
            (".csv",): cls.CSV,
        }
        
        for extensions, file_type in extension_map.items():
            if lower_name.endswith(extensions):
                return file_type
        
        return cls.UNKNOWN

@dataclass
class Statistics:
    """채권 통계 데이터를 담는 컨테이너"""
    yield_df: pd.DataFrame
    spread_df: pd.DataFrame
    
    def to_dict(self) -> dict[str, pd.DataFrame]:
        return {
            'yield': self.yield_df,
            'spread': self.spread_df
        }


@dataclass(frozen=True)
class XPathConfig:
    """XPath 설정값"""
    yield_xpath: str = '//*[@id="con_tab1"]/div[2]'
    spread_xpath: str = '//*[@id="con_tab2"]/div[2]'



@dataclass
class DownloadFile:
    """다운로드 파일 정보"""
    filename: str
    filepath: str
    content: bytes
    file_type: FileType = FileType.UNKNOWN
    downloaded_at: datetime = field(default_factory=datetime.now)

    @property
    def size(self) -> int:
        """파일 크기 (bytes)"""
        return len(self.content)

    @property
    def size_kb(self) -> float:
        """파일 크기 (KB)"""
        return self.size / 1024

    @property
    def size_mb(self) -> float:
        """파일 크기 (MB)"""
        return self.size / (1024 * 1024)

    def is_excel(self) -> bool:
        return self.file_type == FileType.EXCEL

    def is_zip(self) -> bool:
        return self.file_type == FileType.ZIP
