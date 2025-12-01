import re
from typing import List

from ..core.schemas import ContentBlock
from ..interfaces.base_processor import BaseProcessor


class PiiMasker(BaseProcessor):

    component_name = "PiiMasker"

    def initialize(self, mask_email: bool = True, mask_phone: bool = True, **kwargs):
        self.mask_email = mask_email
        self.mask_phone = mask_phone
        self._email_re = re.compile(r"[\w\.-]+@[\w\.-]+")
        # Simple phone regex (customizable)
        self._phone_re = re.compile(r"\d{3}[-\.\s]??\d{3,4}[-\.\s]??\d{4}")

    def _do_process(self, blocks: List[ContentBlock]) -> List[ContentBlock]:
        for block in blocks:
            if block.type not in ["text", "md"] or not isinstance(block.content, str):
                continue

            if self.mask_email:
                block.content = self._email_re.sub("[EMAIL]", block.content)
            if self.mask_phone:
                block.content = self._phone_re.sub("[PHONE]", block.content)

        return blocks
