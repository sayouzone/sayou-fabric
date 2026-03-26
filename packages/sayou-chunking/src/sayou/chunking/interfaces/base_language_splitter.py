"""
Base interface for language-specific code splitters.

Design contract
───────────────
Every language splitter must implement `split()` and return a list of
`SayouChunk` objects whose metadata follows the *standardised key schema*
defined below.  The router (`CodeSplitter`) calls these splitters after
language detection; it never needs to know the internal algorithm.

Standardised metadata keys produced by ALL language splitters
─────────────────────────────────────────────────────────────
Required (always present):
  semantic_type   str  — "function" | "method" | "class_header"
                         | "class_attributes" | "code_block"
  lineStart       int  — 1-based inclusive start line
  lineEnd         int  — 1-based inclusive end line
  language        str  — e.g. "python", "javascript"

Conditional (present when relevant):
  function_name   str  — function or method name
  class_name      str  — class name (for class_header chunks)
  parent_node     str  — owning class name (for method / class_attributes)
  inherits_from   List[str]  — base class names (class_header only)
  calls           List[str]  — directly called symbol names (unresolved)
  attribute_calls List[str]  — `obj.<name>()` call targets (duck-typing)
  type_refs       List[str]  — names from annotations / isinstance checks
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from sayou.core.schemas import SayouBlock, SayouChunk


class BaseLanguageSplitter(ABC):
    """
    [Interface] Every language-specific splitter implements this contract.

    Instances are created on-demand by CodeSplitter; they do NOT inherit
    from BaseComponent and are NOT registered in the component registry.
    They are purely internal implementation details of the code-splitting
    subsystem.
    """

    # ── identity ──────────────────────────────────────────────────────
    language: str = ""  # e.g. "python"
    extensions: List[str] = []  # e.g. [".py"]

    # ── public API ────────────────────────────────────────────────────

    @abstractmethod
    def split(self, doc: SayouBlock, chunk_size: int) -> List[SayouChunk]:
        """
        Split *doc* into structural chunks.

        Args:
            doc:        Normalised SayouBlock (content already str).
            chunk_size: Soft upper bound on content length per chunk.

        Returns:
            List of SayouChunk with standardised metadata (see module doc).
        """
        raise NotImplementedError

    # ── helpers shared by concrete splitters ──────────────────────────

    def _make_chunk(
        self,
        lines: List[str],
        base_meta: dict,
        chunk_index: int,
        extra_meta: Optional[dict] = None,
    ) -> Optional[SayouChunk]:
        """
        Build a SayouChunk from a list of source lines.

        Returns None when the resulting content is empty (after strip).
        """
        content = "\n".join(lines).strip()
        if not content:
            return None

        meta = base_meta.copy()
        meta["chunk_index"] = chunk_index
        meta["language"] = self.language
        if extra_meta:
            meta.update(extra_meta)

        return SayouChunk(content=content, metadata=meta)

    def _flush(
        self,
        chunks: List[SayouChunk],
        lines: List[str],
        base_meta: dict,
        extra_meta: Optional[dict] = None,
    ) -> None:
        """Append a chunk built from *lines* to *chunks* in-place."""
        chunk = self._make_chunk(lines, base_meta, len(chunks), extra_meta)
        if chunk is not None:
            chunks.append(chunk)
