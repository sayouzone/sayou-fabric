# =============================================================================
# Sayou Fabric — Ontology Package
#
# Public API — all consumers import from here:
#   from sayou.core.ontology import SayouClass, SayouPredicate, ...
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

from .base import SayouClassBase, SayouPredicateBase, SayouAttributeBase, SayouEdgeMeta
from .code import SayouClassCode, SayouPredicateCode, SayouAttributeCode
from .document import SayouClassDocument, SayouPredicateDocument, SayouAttributeDocument
from .media import SayouClassMedia, SayouPredicateMedia, SayouAttributeMedia


class SayouClass(SayouClassBase, SayouClassCode, SayouClassDocument, SayouClassMedia):
    """Unified node type labels — all domains merged."""

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
    # Domain-specific classes for consumers that want explicit imports
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
