class SayouClass:
    """Ontology Class Definitions"""

    TOPIC = "sayou:Topic"
    TABLE = "sayou:Table"
    CODE = "sayou:Code"
    TEXT = "sayou:TextFragment"
    LIST_ITEM = "sayou:ListItem"


class SayouPredicate:
    """Relationship Definitions"""

    HAS_PARENT = "sayou:hasParent"
    NEXT = "sayou:next"
    MENTIONS = "sayou:mentions"


class SayouAttribute:
    """Property Keys"""

    TEXT = "schema:text"
    SEMANTIC_TYPE = "sayou:semanticType"
    PAGE_INDEX = "sayou:pageIndex"
    PART_INDEX = "sayou:partIndex"
    SOURCE = "sayou:source"
