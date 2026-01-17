# Copyright (c) 2025-2026, Sayouzone
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
 
"""
Base Crawler
===========================

Base Crawler에서 주요 데이터를 추출하는 Python 패키지

Installation:
    pip install requests beautifulsoup4 lxml
"""

__version__ = "0.2.0"
__author__ = "SeongJung Kim"

from .client import BaseClient

__all__ = [
    # 메인 클래스
    "BaseClient",
    
    # 데이터 모델
    
    # 파서
]
