"""
CodeSplitter — Polyglot code splitting router.

Responsibility
──────────────
This class is the single registered component for code splitting.
It does NOT contain any language-specific parsing logic.
Its only job is:

  1. Detect the programming language from file extension or explicit strategy.
  2. Instantiate the correct language-specific splitter.
  3. Delegate splitting and return standardised SayouChunks.

Adding a new language
─────────────────────
Implement `BaseLanguageSplitter` in `languages/<lang>_splitter.py`, then add
an instance to `languages/__init__.LANGUAGE_SPLITTERS`.  No changes to this
file are needed.
"""

from typing import Any, Dict, List, Optional

from sayou.core.registry import register_component
from sayou.core.schemas import SayouBlock, SayouChunk

from ..interfaces.base_language_splitter import BaseLanguageSplitter
from ..interfaces.base_splitter import BaseSplitter
from ..languages import LANGUAGE_SPLITTERS


@register_component("splitter")
class CodeSplitter(BaseSplitter):
    """
    Polyglot code splitter — routes to the correct language-specific engine.

    Strategy values accepted by `can_handle`:
      "code"          — accept any code file (auto-detect language)
      "python"        — force Python AST splitter
      "javascript"    — force JavaScript splitter
      "typescript"    — force TypeScript splitter
      "java"          — force Java splitter
      "go"            — force Go splitter
      "<extension>"   — e.g. ".py", ".ts"  (normalised automatically)
    """

    component_name = "CodeSplitter"

    # Build a lookup table: extension (with dot, lowercase) → splitter instance
    _EXT_MAP: Dict[str, BaseLanguageSplitter] = {}
    _LANG_MAP: Dict[str, BaseLanguageSplitter] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

    # Class-level initialisation of the lookup maps
    @classmethod
    def _build_maps(cls):
        for splitter in LANGUAGE_SPLITTERS:
            cls._LANG_MAP[splitter.language] = splitter
            for ext in splitter.extensions:
                cls._EXT_MAP[ext.lower()] = splitter

    @classmethod
    def can_handle(cls, input_data: Any, strategy: str = "auto") -> float:
        if not cls._EXT_MAP:
            cls._build_maps()

        if strategy == "code":
            return 1.0
        # Explicit language name
        if strategy in cls._LANG_MAP:
            return 1.0
        # Extension passed as strategy (e.g. ".py")
        if strategy.startswith(".") and strategy.lower() in cls._EXT_MAP:
            return 1.0
        # Auto: check file extension in metadata
        meta = (
            getattr(input_data, "metadata", {})
            if not isinstance(input_data, dict)
            else input_data.get("metadata", {})
        )
        ext = meta.get("extension", "").lower()
        if ext in cls._EXT_MAP:
            return 1.0
        return 0.0

    # ── template method hook ──────────────────────────────────────────

    def _do_split(self, doc: SayouBlock) -> List[SayouChunk]:
        if not self._EXT_MAP:
            self._build_maps()

        config = doc.metadata.get("config", {})
        chunk_size = int(config.get("chunk_size", 1500))
        strategy = config.get("strategy", "auto")

        splitter = self._resolve_splitter(doc, strategy)

        if splitter is None:
            self._log(
                f"⚠️ No language splitter found for strategy='{strategy}', "
                f"extension='{doc.metadata.get('extension', '')}'. "
                f"Falling back to Python splitter.",
                level="warning",
            )
            splitter = self._LANG_MAP.get("python")
            if splitter is None:
                return []

        self._log(
            f"🔀 Routing to [{splitter.language}] splitter "
            f"(source: {doc.metadata.get('source', '?')}, "
            f"size: {len(doc.content)} chars)"
        )

        chunks = splitter.split(doc, chunk_size)
        self._log(f"✅ [{splitter.language}] produced {len(chunks)} chunks.")
        return chunks

    # ── internal helpers ──────────────────────────────────────────────

    def _resolve_splitter(
        self, doc: SayouBlock, strategy: str
    ) -> Optional[BaseLanguageSplitter]:
        """
        Priority order:
          1. Explicit language strategy  (e.g. "python")
          2. Extension-as-strategy       (e.g. ".py")
          3. Extension from metadata     (e.g. metadata["extension"] == ".py")
          4. None  → caller applies fallback
        """
        # 1. Explicit language
        if strategy in self._LANG_MAP:
            return self._LANG_MAP[strategy]

        # 2. Extension string passed as strategy
        if strategy.startswith("."):
            splitter = self._EXT_MAP.get(strategy.lower())
            if splitter:
                return splitter

        # 3. Metadata extension
        ext = doc.metadata.get("extension", "").lower()
        if ext:
            # Normalise: ensure leading dot
            if not ext.startswith("."):
                ext = f".{ext}"
            splitter = self._EXT_MAP.get(ext)
            if splitter:
                return splitter

        return None


# Trigger map construction at import time
CodeSplitter._build_maps()
