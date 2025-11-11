from typing import List, Any
from ..interfaces.base_generator import BaseGenerator
import re
from urllib.parse import urljoin

class HtmlLinkGenerator(BaseGenerator):
    """(Tier 2) 'HTML(str)'에서 <a> 태그를 추출하는 일반 엔진."""
    component_name = "HtmlLinkGenerator"

    def initialize(self, **kwargs):
        # (간단한 예시: v.0.0.1에서는 모든 링크 추출)
        # (v.0.1.0: 'allow_domains', 'deny_patterns' 등 kwargs 추가)
        self.base_url = kwargs.get("base_url", "") # 상대 경로 변환용
        self._link_re = re.compile(r'href=["\'](.[^"\']+)["\']')

    def _do_generate(self, raw_data: Any) -> List[str]:
        if not isinstance(raw_data, str):
            return []
        
        # (v.0.0.1 에서는 base_url을 seed에서 받아오도록 pipeline이 설정해야 함)
        # (여기서는 임시로 base_url을 사용)
        
        links = self._link_re.findall(raw_data)
        # 상대 경로(e.g., /subpage)를 절대 경로로 변환
        return [urljoin(self.base_url, link) for link in links if link.startswith(('/', 'http'))]