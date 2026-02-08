class SayouClass:
    """Ontology Class Definitions (Standard Types)"""

    # Base
    TOPIC = "sayou:Topic"
    DOCUMENT = "sayou:Document"
    CHUNK = "sayou:Chunk"

    # Domain: Document
    TABLE = "sayou:Table"
    CODE_BLOCK = "sayou:CodeBlock"
    TEXT = "sayou:TextFragment"
    LIST_ITEM = "sayou:ListItem"

    # Domain: Code
    FILE = "sayou:File"
    CLASS = "sayou:Class"
    FUNCTION = "sayou:Function"
    METHOD = "sayou:Method"
    LIBRARY = "sayou:Library"
    ATTRIBUTE_BLOCK = "sayou:AttributeBlock"

    # Domain: Media (YouTube)
    VIDEO = "sayou:Video"
    VIDEO_SEGMENT = "sayou:VideoSegment"


class SayouPredicate:
    """Relationship Definitions (Standard Edges)"""

    # Base
    HAS_PARENT = "sayou:hasParent"
    NEXT = "sayou:next"
    CONTAINS = "sayou:contains"
    BELONGS_TO = "sayou:belongsTo"
    MENTIONS = "sayou:mentions"

    # Domain: Code
    DEFINED_IN = "sayou:definedIn"
    IMPORTS = "sayou:imports"
    CALLS = "sayou:calls"


class SayouAttribute:
    """Property Keys (Standard Attributes)"""

    # Base
    TEXT = "schema:text"
    SOURCE = "sayou:source"
    TITLE = "sayou:title"

    # Document/Code Common
    SEMANTIC_TYPE = "sayou:semanticType"
    FILE_PATH = "sayou:filePath"
    LINE_START = "sayou:lineStart"

    # Domain: Document
    PAGE_INDEX = "sayou:pageIndex"
    PART_INDEX = "sayou:partIndex"

    # Domain: Media
    START_TIME = "sayou:startTime"
    END_TIME = "sayou:endTime"
    DURATION = "sayou:duration"
