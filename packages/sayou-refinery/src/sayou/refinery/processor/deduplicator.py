import json
from typing import List, Set

from ..core.schemas import ContentBlock
from ..interfaces.base_processor import BaseProcessor


class Deduplicator(BaseProcessor):

    component_name = "Deduplicator"

    def _do_process(self, blocks: List[ContentBlock]) -> List[ContentBlock]:
        seen_hashes: Set[int] = set()
        unique_blocks: List[ContentBlock] = []

        for block in blocks:
            # Generate stable hash key
            if isinstance(block.content, dict):
                content_str = json.dumps(block.content, sort_keys=True)
            else:
                content_str = str(block.content)

            if len(content_str) < 5:
                unique_blocks.append(block)
                continue

            content_hash = hash(content_str)

            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_blocks.append(block)

        return unique_blocks
