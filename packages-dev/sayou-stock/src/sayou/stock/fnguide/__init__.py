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
 
"""
FnGuide Crawler
===========================

FnGuide에서 주요 데이터를 추출하는 Python 패키지

Installation:
    pip install requests beautifulsoup4 lxml

Quick Start:
    >>> from fnguide import FnGuideCrawler
    >>> 
    >>> crawler = FnGuideCrawler()
    >>> 
    >>> # FnGuide 기업 정보 | Snapshot 조회
    >>> data = crawler.main("005930")
    >>> print(data)
    >>> 
    >>> # FnGuide 기업 정보 | 재무제표 조회
    >>> data = crawler.finance("005930")
    >>> print(data)

Supported Informations:
    - FnGuide 기업 정보 | Snapshot
    - FnGuide 기업 정보 | 재무제표
    - FnGuide 기업 정보 | 기업개요
    - FnGuide 기업 정보 | 경쟁사비교
    - FnGuide 기업 정보 | 컨센서스
    - FnGuide 기업 정보 | 금감원공시
    - FnGuide 기업 정보 | 거래소공시
    - FnGuide 기업 정보 | 재무비율
    - FnGuide 기업 정보 | 재무제표
    - FnGuide 기업 정보 | 업종분석
    - FnGuide 기업 정보 | 투자지표
    - FnGuide 기업 정보 | 지분분석

Note:
    FnGuide에서 User-Agent 헤더를 요구합니다. 
"""

__version__ = "0.1.0"
__author__ = "SeongJung Kim"

from .crawler import FnGuideCrawler
from .client import FnGuideClient
#from .models import (
#    # 공통
#    DartConfig,
#)
from .parsers import (
    FnGuideCompanyParser,
    FnGuideComparisonParser,
    FnGuideConsensusParser,
    FnGuideDartParser,
    FnGuideDisclosureParser,
    FnGuideFinanceRatioParser,
    FnGuideFinanceParser,
    FnGuideIndustryAnalysisParser,
    FnGuideInvestParser,
    FnGuideMainParser,
    FnGuideShareAnalysisParser,
)

__all__ = [
    # 메인 클래스
    "FnGuideCrawler",
    "FnGuideClient",
    
    # 데이터 모델
    #"DartConfig",
    
    # 파서
    "FnGuideCompanyParser",
    "FnGuideComparisonParser",
    "FnGuideConsensusParser",
    "FnGuideDartParser",
    "FnGuideDisclosureParser",
    "FnGuideFinanceRatioParser",
    "FnGuideFinanceParser",
    "FnGuideIndustryAnalysisParser",
    "FnGuideInvestParser",
    "FnGuideMainParser",
    "FnGuideShareAnalysisParser",
]
