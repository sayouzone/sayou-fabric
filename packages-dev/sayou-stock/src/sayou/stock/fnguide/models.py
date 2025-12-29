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

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

@dataclass
class TableData:
    """테이블 데이터 컨테이너"""
    
    caption: str = ""
    headers: List[str] = field(default_factory=list)
    data: Dict[str, List[str]] = field(default_factory=dict)
    # 2레벨 키 지원: {(카테고리, 항목): [값들]}
    data_with_category: Dict[Tuple[str, str], List[str]] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환 (JSON 직렬화용)"""
        result = {
            "caption": self.caption,
            "headers": self.headers,
        }
        
        if self.data:
            result["data"] = self.data
        
        if self.data_with_category:
            result["data_with_category"] = {
                f"{cat}|{item}": values 
                for (cat, item), values in self.data_with_category.items()
            }
        
        return result
    
    def get_value(self, key: str, header: str) -> Optional[str]:
        """특정 항목의 특정 헤더 값 조회"""
        if key not in self.data:
            return None
        try:
            idx = self.headers.index(header)
            return self.data[key][idx]
        except (ValueError, IndexError):
            return None


@dataclass 
class KeyValueData:
    """키-값 형태 테이블 데이터 (General Information 등)"""
    
    caption: str = ""
    data: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "caption": self.caption,
            "data": self.data
        }


@dataclass
class HistoryData:
    """연혁 테이블 데이터"""
    
    caption: str = ""
    headers: List[str] = field(default_factory=list)
    records: List[Dict[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "caption": self.caption,
            "headers": self.headers,
            "records": self.records
        }

@dataclass
class FinancialRatioData:
    """재무비율 데이터 컨테이너"""
    
    categories: List[str] = field(default_factory=list)
    periods: List[str] = field(default_factory=list)
    data: Dict[Tuple[str, str], List[str]] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환 (JSON 직렬화용)"""
        return {
            "categories": self.categories,
            "periods": self.periods,
            "data": {f"{cat}|{item}": values for (cat, item), values in self.data.items()}
        }
    
    def get_value(self, category: str, item: str, period: str) -> Optional[str]:
        """특정 항목의 특정 기간 값 조회"""
        key = (category, item)
        if key not in self.data:
            return None
        try:
            idx = self.periods.index(period)
            return self.data[key][idx]
        except (ValueError, IndexError):
            return None