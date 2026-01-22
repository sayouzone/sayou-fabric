import re
from typing import List

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock

from ..interfaces.base_processor import BaseProcessor


@register_component("processor")
class LinkProcessor(BaseProcessor):
    """
    Extracts URLs/Links from text and moves them to metadata,
    and optionally removes them from the content to clean up text.

    Supports: Raw URLs, Markdown links [text](url)
    """

    component_name = "LinkProcessor"

    def _do_process(self, blocks: List[SayouBlock]) -> List[SayouBlock]:
        remove_links = self.config.get("remove_links", False)

        # URL regex (http/https)
        url_pattern = r"(https?://[^\s)\]]+)"
        # Markdown link regex [text](url) -> group1: text, group2: url
        md_link_pattern = r"\[([^\]]+)\]\((https?://[^\s)]+)\)"

        for block in blocks:
            if block.type != "text" or not isinstance(block.content, str):
                continue

            text = block.content
            found_links = []

            # 1. Find Markdown links
            matches = re.findall(md_link_pattern, text)
            for title, url in matches:
                found_links.append({"title": title, "url": url})

            # 2. Find Raw URLs (not included in Markdown)
            # (For simplicity, duplicate handling is omitted or fine-tuning is needed)
            raw_matches = re.findall(url_pattern, text)
            for url in raw_matches:
                # Add if not already found
                if not any(l["url"] == url for l in found_links):
                    found_links.append({"title": "raw_link", "url": url})

            # 3. Extract links to metadata
            if found_links:
                if "links" not in block.metadata:
                    block.metadata["links"] = []
                block.metadata["links"].extend(found_links)

            # 4. (Option) Remove links from text
            if remove_links:
                # Markdown links are left as text: [Google](...) -> Google
                text = re.sub(md_link_pattern, r"\1", text)
                # Remaining Raw URLs are removed
                text = re.sub(url_pattern, "", text)
                # Clean up whitespace
                block.content = re.sub(r"\s+", " ", text).strip()

        return blocks
