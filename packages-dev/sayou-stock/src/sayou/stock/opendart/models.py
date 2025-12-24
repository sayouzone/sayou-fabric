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
 
import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass(frozen=True)
class DartConfig:
    """DART 크롤러 설정."""
    
    bucket_name: str
    api_key: str
    
    @classmethod
    def from_env(cls) -> "DartConfig":
        """환경 변수에서 설정을 로드합니다."""

        load_dotenv()

        bucket_name = "sayouzone-ai-stocks"
        api_key = os.environ.get("DART_API_KEY", "")
        #api_key = "fd664865257f1a3073b654f9185de11a708f726c"
        
        if not api_key:
            raise ValueError("DART_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        return cls(bucket_name=bucket_name, api_key=api_key)