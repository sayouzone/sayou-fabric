# =============================================================================
# Sayou Fabric — Document Domain Ontology
#
# Node types, edge types, and property keys for document knowledge graphs.
# Consumed by: sayou-chunking (document splitters), sayou-wrapper (doc adapters)
# =============================================================================


class SayouClassDocument:
    """Node type labels for the document domain."""

    TABLE = "sayou:Table"
    TEXT = "sayou:TextFragment"
    LIST_ITEM = "sayou:ListItem"


class SayouPredicateDocument:
    """Edge type labels for the document domain."""

    # Reserved for future document-specific relationships.
    pass


class SayouAttributeDocument:
    """Property key constants for the document domain."""

    PAGE_INDEX = "sayou:pageIndex"
    PART_INDEX = "sayou:partIndex"
