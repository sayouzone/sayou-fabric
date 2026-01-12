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

from io import StringIO
from typing import Optional

import pandas as pd
from lxml import html


class HtmlTableExtractor:
    """HTML에서 테이블을 추출하는 유틸리티 클래스"""

    @staticmethod
    def extract_by_xpath(html_string: str, xpath_expr: str) -> Optional[pd.DataFrame]:
        """
        XPath로 지정된 영역에서 테이블을 추출합니다.
        
        Args:
            html_string: HTML 문자열
            xpath_expr: XPath 표현식
            
        Returns:
            추출된 DataFrame 또는 None
        """
        tree = html.fromstring(html_string)
        elements = tree.xpath(xpath_expr)

        if not elements:
            return None

        element_html = html.tostring(elements[0], encoding="unicode")
        tables = pd.read_html(StringIO(element_html))

        return tables[0] if tables else None

    @staticmethod
    def extract_all_tables(html_string: str) -> list[pd.DataFrame]:
        """
        HTML에서 모든 테이블을 추출합니다.
        
        Args:
            html_string: HTML 문자열
            
        Returns:
            DataFrame 리스트
        """
        try:
            return pd.read_html(StringIO(html_string))
        except ValueError:
            return []

    @staticmethod
    def extract_text_by_xpath(html_string: str, xpath_expr: str) -> Optional[str]:
        """
        XPath로 지정된 영역에서 텍스트를 추출합니다.
        
        Args:
            html_string: HTML 문자열
            xpath_expr: XPath 표현식
            
        Returns:
            추출된 텍스트 또는 None
        """
        tree = html.fromstring(html_string)
        elements = tree.xpath(xpath_expr)

        if not elements:
            return None

        return elements[0].text_content()