"""
Go language splitter — stub implementation.

Status: STUB
─────────────
Regex detects top-level func / type / struct declarations.
Call-graph extraction pending go/ast integration (future work).
"""

import re
from typing import List

from sayou.core.schemas import SayouBlock, SayouChunk

from ..interfaces.base_language_splitter import BaseLanguageSplitter


class GoSplitter(BaseLanguageSplitter):
    """Regex-based structural splitter for Go source files."""

    language = "go"
    extensions = [".go"]

    _SEPARATORS = [
        r"(\nfunc\s+)",
        r"(\ntype\s+)",
        r"(\nvar\s+)",
        r"(\nconst\s+)",
        r"(\n\n+)",
        r"(\n+)",
    ]

    def split(self, doc: SayouBlock, chunk_size: int) -> List[SayouChunk]:
        chunks: List[SayouChunk] = []
        base_meta = doc.metadata.copy()
        for i, text in enumerate(
            self._recursive_split(doc.content, self._SEPARATORS, chunk_size)
        ):
            if text.strip():
                meta = base_meta.copy()
                meta.update(
                    {
                        "chunk_index": i,
                        "semantic_type": "code_block",
                        "language": self.language,
                        # TODO: go/ast-based call-graph extraction
                    }
                )
                chunks.append(SayouChunk(content=text, metadata=meta))
        return chunks

    def _recursive_split(self, text, separators, chunk_size):
        if len(text) <= chunk_size or not separators:
            return [text]
        try:
            splits = re.split(separators[0], text)
        except Exception:
            return self._recursive_split(text, separators[1:], chunk_size)
        if len(splits) < 3:
            return self._recursive_split(text, separators[1:], chunk_size)
        merged = [splits[0]] if splits[0] else []
        for i in range(1, len(splits), 2):
            merged.append(splits[i] + (splits[i + 1] if i + 1 < len(splits) else ""))
        result, buf, buf_len = [], [], 0
        for s in merged:
            if len(s) > chunk_size:
                if buf:
                    result.append("".join(buf))
                    buf, buf_len = [], 0
                result.extend(self._recursive_split(s, separators[1:], chunk_size))
            elif buf_len + len(s) > chunk_size:
                result.append("".join(buf))
                buf, buf_len = [s], len(s)
            else:
                buf.append(s)
                buf_len += len(s)
        if buf:
            result.append("".join(buf))
        return result
