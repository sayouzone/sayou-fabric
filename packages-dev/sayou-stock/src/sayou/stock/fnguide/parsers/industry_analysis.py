import requests

from ..client import FnGuideClient

from ..utils import (
    urls
)

class FnGuideIndustryAnalysisParser:
    """
    FnGuide 업종분석 파싱 클래스
    
    Snapshot, https://comp.fnguide.com/SVO2/ASP/SVD_ujanal.asp?gicode=A{stock}
    """

    def __init__(self, client: FnGuideClient):
        self.client = client
    
    def parse(self, stock: str):
        """
        기업 정보 | 업종분석 정보 추출 후 주요 키를 영어로 변환
        requests로 HTML을 가져온 후 pandas.read_html()로 파싱

        Args:
            html_text (str): HTML text
            stock: 종목 코드 (회사명을 "company"로 치환하기 위해 사용)

        Returns:
            Dict: 컬럼명이 번역된 DataFrame
        """

        url = urls.get("업종분석")

        if not url:
            return
        
        params = {
            "gicode": f"A{stock}"
        }

        try:
            response = self.client._get(url, params=params)
        except requests.RequestException as e:
            logger.error(f"페이지 요청 실패: {e}")
            return None

        frames = pd.read_html(StringIO(response.text))

        return None