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

    # Domain: Code — Structural
    DEFINED_IN = "sayou:definedIn"
    IMPORTS = "sayou:imports"
    CONTAINS = "sayou:contains"  # File → Class/Function, Class → Method

    # Domain: Code — Behavioral
    CALLS = "sayou:calls"  # Direct call (resolved to known symbol)
    MAYBE_CALLS = (
        "sayou:maybeCalls"  # Probable call (duck-typing / attr access, unresolved)
    )

    # Domain: Code — Inheritance
    INHERITS = "sayou:inherits"  # Class → Parent Class
    OVERRIDES = "sayou:overrides"  # Method → Parent Method (same name, different class)

    # Domain: Code — Type / Protocol
    USES_TYPE = "sayou:usesType"  # Weak structural coupling (isinstance / annotation)


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
    LINE_END = "sayou:lineEnd"

    # Domain: Document
    PAGE_INDEX = "sayou:pageIndex"
    PART_INDEX = "sayou:partIndex"

    # Domain: Code — Identity
    SYMBOL_NAME = "sayou:symbolName"  # canonical name (function/class)
    PARENT_CLASS = "sayou:parentClass"  # for methods: owning class name
    LANGUAGE = "sayou:language"  # python / javascript / ...

    # Domain: Code — Call graph raw data (pre-edge-resolution)
    CALLS_RAW = "sayou:callsRaw"  # List[str] of direct call names extracted by AST
    ATTR_CALLS_RAW = (
        "sayou:attrCallsRaw"  # List[str] of obj.method() attribute call names
    )
    INHERITS_FROM_RAW = (
        "sayou:inheritsFromRaw"  # List[str] of base class names (string)
    )
    TYPE_REFS_RAW = (
        "sayou:typeRefsRaw"  # List[str] from annotations / isinstance checks
    )

    # Domain: Media
    START_TIME = "sayou:startTime"
    END_TIME = "sayou:endTime"
    DURATION = "sayou:duration"


class SayouEdgeMeta:
    """Standard metadata keys carried on edges (stored in edge dict)."""

    CONFIDENCE = "confidence"  # "HIGH" | "MEDIUM" | "LOW"
    RESOLUTION = "resolution"  # "DIRECT" | "INFERRED" | "HEURISTIC"
    EDGE_SOURCE = "edge_source"  # which builder generated this edge
