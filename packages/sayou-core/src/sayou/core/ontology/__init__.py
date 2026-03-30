# =============================================================================
# Sayou Fabric — Ontology Package
#
# Public API — all consumers import from here:
#   from sayou.core.ontology import SayouClass, SayouPredicate, SayouAttribute
#
# Internal layout:
#   base.py      — domain-agnostic foundations
#   code.py      — code domain
#   document.py  — document domain
#   media.py     — media domain
#
# Flat facades (SayouClass, SayouPredicate, SayouAttribute) merge all domain
# classes into a single namespace so existing code requires zero changes.
# =============================================================================

from .base import (SayouAttributeBase, SayouClassBase, SayouEdgeMeta,
                   SayouPredicateBase)
from .code import SayouAttributeCode, SayouClassCode, SayouPredicateCode
from .document import (SayouAttributeDocument, SayouClassDocument,
                       SayouPredicateDocument)
from .media import SayouAttributeMedia, SayouClassMedia, SayouPredicateMedia


class SayouClass(SayouClassBase, SayouClassCode, SayouClassDocument, SayouClassMedia):
    """
    Unified node type labels — all domains merged.

    Naming conventions
    ──────────────────
    Constant names match the concept, not the URI value:

        SayouClass.TEXT_FRAGMENT  →  "sayou:TextFragment"
        SayouClass.CODE_BLOCK     →  "sayou:CodeBlock"
        SayouClass.VIDEO_SEGMENT  →  "sayou:VideoSegment"
    """

    pass


class SayouPredicate(
    SayouPredicateBase,
    SayouPredicateCode,
    SayouPredicateDocument,
    SayouPredicateMedia,
):
    """Unified edge type labels — all domains merged."""

    pass


class SayouAttribute(
    SayouAttributeBase,
    SayouAttributeCode,
    SayouAttributeDocument,
    SayouAttributeMedia,
):
    """Unified property key constants — all domains merged."""

    pass


__all__ = [
    "SayouClass",
    "SayouPredicate",
    "SayouAttribute",
    "SayouEdgeMeta",
    # Domain-specific classes for explicit imports
    "SayouClassBase",
    "SayouPredicateBase",
    "SayouAttributeBase",
    "SayouClassCode",
    "SayouPredicateCode",
    "SayouAttributeCode",
    "SayouClassDocument",
    "SayouPredicateDocument",
    "SayouAttributeDocument",
    "SayouClassMedia",
    "SayouPredicateMedia",
    "SayouAttributeMedia",
]
