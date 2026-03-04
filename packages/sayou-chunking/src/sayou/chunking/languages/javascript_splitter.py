"""
JavaScript language splitter — stub implementation.

Status: STUB
─────────────
Regex-based structural split is functional (classes, functions, arrow functions).
Call-graph extraction (calls / attribute_calls) is NOT yet implemented.
To complete: parse a JS AST (e.g. via an external tool or embedded parser)
and mirror the pattern of PythonSplitter._extract_calls().
"""

import re
from typing import List

from sayou.core.schemas import SayouBlock, SayouChunk

from ..interfaces.base_language_splitter import BaseLanguageSplitter


class JavaScriptSplitter(BaseLanguageSplitter):
    """Regex-based structural splitter for JavaScript / JSX."""

    language = "javascript"
    extensions = [".js", ".jsx", ".mjs", ".cjs"]

    _SEPARATORS = [
        r"(\n\s*class\s+)",
        r"(\n\s*function\s+)",
        r"(\n\s*const\s+\w+\s*=\s*(?:async\s+)?(?:function|\())",
        r"(\n\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+)",
        r"(\n\n+)",
        r"(\n+)",
    ]

    def split(self, doc: SayouBlock, chunk_size: int) -> List[SayouChunk]:
        chunks: List[SayouChunk] = []
        base_meta = doc.metadata.copy()
        texts = self._regex_split(doc.content, chunk_size)
        for i, text in enumerate(texts):
            if text.strip():
                meta = base_meta.copy()
                meta.update(
                    {
                        "chunk_index": i,
                        "semantic_type": "code_block",
                        "language": self.language,
                        # TODO: extract calls, attribute_calls via JS AST
                    }
                )
                chunks.append(SayouChunk(content=text, metadata=meta))
        return chunks

    def _regex_split(self, text: str, chunk_size: int) -> List[str]:
        return self._recursive_split(text, self._SEPARATORS, chunk_size)

    def _recursive_split(
        self, text: str, separators: List[str], chunk_size: int
    ) -> List[str]:
        if len(text) <= chunk_size or not separators:
            return [text]
        pattern = separators[0]
        rest = separators[1:]
        try:
            splits = re.split(pattern, text)
        except Exception:
            return self._recursive_split(text, rest, chunk_size)
        if len(splits) < 3:
            return self._recursive_split(text, rest, chunk_size)
        merged = [splits[0]] if splits[0] else []
        for i in range(1, len(splits), 2):
            merged.append(splits[i] + (splits[i + 1] if i + 1 < len(splits) else ""))
        result: List[str] = []
        buf: List[str] = []
        buf_len = 0
        for s in merged:
            if len(s) > chunk_size:
                if buf:
                    result.append("".join(buf))
                    buf, buf_len = [], 0
                result.extend(self._recursive_split(s, rest, chunk_size))
            elif buf_len + len(s) > chunk_size:
                result.append("".join(buf))
                buf, buf_len = [s], len(s)
            else:
                buf.append(s)
                buf_len += len(s)
        if buf:
            result.append("".join(buf))
        return result
