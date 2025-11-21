import copy
import re

from ..core.context import RefineryContext
from ..interfaces.base_processor import BaseProcessor

class DefaultTextCleaner(BaseProcessor):
    """
    (Tier 2) '일반 텍스트 처리' 엔진.
    Atom의 payload에서 'target_field'를 찾아 HTML 태그와
    여분의 공백을 제거합니다.
    """
    component_name = "DefaultTextCleaner"

    def initialize(self, **kwargs):
        # 사용자가 `target_field`를 지정하지 않으면 'text_content'를 기본값으로 사용
        self.target_field = kwargs.get("target_field", "text_content")
        self._html_tag_re = re.compile(r'<[^>]+>')
        self._whitespace_re = re.compile(r'\s+')
        self._log(f"Initialized to clean field: '{self.target_field}'")

    def process(self, context: RefineryContext) -> RefineryContext:
        atoms = context.atoms
        self._log(f"Running DefaultTextCleaner on {len(atoms)} atoms...")
        processed_atoms = []
        for atom in atoms:
            atom_copy = copy.deepcopy(atom)
            payload = atom_copy.payload
            
            if self.target_field in payload:
                try:
                    cleaned_text = self._clean(payload[self.target_field])
                    payload[self.target_field] = cleaned_text
                    processed_atoms.append(atom_copy)
                except Exception as e:
                    self._log(f"Failed to clean atom {atom.atom_id}: {e}")
            else:
                # 필드가 없으면 (정제할 것이 없으면) 그대로 통과
                processed_atoms.append(atom_copy)
                
        context.atoms = processed_atoms # 2. 컨텍스트의 Atom을 교체한다
        return context

    def _clean(self, text: str) -> str:
        if not isinstance(text, str):
            return text
        text = self._html_tag_re.sub('', text)
        text = self._whitespace_re.sub(' ', text).strip()
        return text