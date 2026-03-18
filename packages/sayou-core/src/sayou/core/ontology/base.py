# =============================================================================
# Sayou Fabric — Base Ontology
#
# Domain-agnostic types, predicates, and attributes shared across all domains.
# New domain files (code.py, document.py, ...) extend these foundations.
# =============================================================================


class SayouClassBase:
    """Base node type labels shared across all domains."""

    TOPIC = "sayou:Topic"
    DOCUMENT = "sayou:Document"
    CHUNK = "sayou:Chunk"


class SayouPredicateBase:
    """Base edge type labels shared across all domains."""

    HAS_PARENT = "sayou:hasParent"  # generic parent link
    NEXT = "sayou:next"  # sequential ordering
    CONTAINS = "sayou:contains"  # structural containment
    BELONGS_TO = "sayou:belongsTo"
    MENTIONS = "sayou:mentions"


class SayouAttributeBase:
    """Base property keys shared across all domains."""

    TEXT = "schema:text"
    SOURCE = "sayou:source"
    TITLE = "sayou:title"
    SEMANTIC_TYPE = "sayou:semanticType"
    FILE_PATH = "sayou:filePath"
    LINE_START = "sayou:lineStart"
    LINE_END = "sayou:lineEnd"


class SayouEdgeMeta:
    """Standard metadata keys carried on every edge dict."""

    CONFIDENCE = "confidence"  # "HIGH" | "MEDIUM" | "LOW"
    RESOLUTION = "resolution"  # "DIRECT" | "INFERRED" | "HEURISTIC"
    EDGE_SOURCE = "edge_source"  # which builder/resolver generated this edge
