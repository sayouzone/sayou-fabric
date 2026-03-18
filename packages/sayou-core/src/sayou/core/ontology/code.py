# =============================================================================
# Sayou Fabric — Code Domain Ontology
#
# Node types, edge types, and property keys specific to code knowledge graphs.
# Consumed by: sayou-chunking, sayou-wrapper, sayou-assembler
# =============================================================================


class SayouClassCode:
    """Node type labels for the code domain."""

    FILE = "sayou:File"
    CLASS = "sayou:Class"
    FUNCTION = "sayou:Function"
    METHOD = "sayou:Method"
    CODE_BLOCK = "sayou:CodeBlock"  # loose / unclassified block
    ATTRIBUTE_BLOCK = "sayou:AttributeBlock"  # class-level attribute assignments
    LIBRARY = "sayou:Library"


class SayouPredicateCode:
    """Edge type labels for the code domain."""

    # ── Structural ────────────────────────────────────────────────────────────
    DEFINED_IN = "sayou:definedIn"  # node → File it is defined in
    IMPORTS = "sayou:imports"  # File/Block → File/Symbol it imports

    # ── Behavioral ────────────────────────────────────────────────────────────
    CALLS = "sayou:calls"  # Func/Method → Func/Method  (resolved, HIGH)
    MAYBE_CALLS = "sayou:maybeCalls"  # Func/Method → Func/Method  (duck-type, LOW)

    # ── Inheritance ───────────────────────────────────────────────────────────
    INHERITS = "sayou:inherits"  # Class → Parent Class
    OVERRIDES = "sayou:overrides"  # Method → Parent Method (same name, child class)

    # ── Type coupling ─────────────────────────────────────────────────────────
    USES_TYPE = "sayou:usesType"  # Func/Method → Class  (annotation / isinstance)

    # ── Global state ──────────────────────────────────────────────────────────
    MUTATES_GLOBAL = "sayou:mutatesGlobal"  # Func/Method → CodeBlock (module-level var)

    # ── Exception contract ────────────────────────────────────────────────────
    RAISES = "sayou:raises"  # Func/Method → virtual exc node (sayou:exc:<n>)

    # ── Public interface ──────────────────────────────────────────────────────
    EXPOSES = "sayou:exposes"  # File → Func/Class declared in __all__


class SayouAttributeCode:
    """Property key constants for the code domain."""

    # ── Identity ──────────────────────────────────────────────────────────────
    SYMBOL_NAME = "sayou:symbolName"  # canonical name (function / class)
    PARENT_CLASS = "sayou:parentClass"  # owning class name (methods only)
    LANGUAGE = "sayou:language"  # "python" | "javascript" | ...

    # ── Call graph (raw, pre-resolution) ─────────────────────────────────────
    CALLS_RAW = "sayou:callsRaw"
    # List[str] direct call names extracted by AST

    ATTR_CALLS_RAW = "sayou:attrCallsRaw"
    # List[str] obj.method() attribute call names

    INHERITS_FROM_RAW = "sayou:inheritsFromRaw"
    # List[str] base class names

    TYPE_REFS_RAW = "sayou:typeRefsRaw"
    # List[str] names from annotations / isinstance checks

    DECORATORS_RAW = "sayou:decoratorsRaw"
    # List[str] decorator names applied to this node

    # ── Global state ──────────────────────────────────────────────────────────
    MODULE_VARS_RAW = "sayou:moduleVarsRaw"
    # List[str] variable names assigned at module level (loose blocks)

    GLOBALS_DECLARED_RAW = "sayou:globalsDeclaredRaw"
    # List[str] names from `global x` inside a function — direct mutation signal

    # ── Public interface ──────────────────────────────────────────────────────
    MODULE_ALL_RAW = "sayou:moduleAllRaw"
    # List[str] names declared in __all__ — present on FILE node

    # ── Exception flow ────────────────────────────────────────────────────────
    RAISES_RAW = "sayou:raisesRaw"
    # List[str] exception type names from raise statements (bare raise excluded)

    CATCHES_RAW = "sayou:catchesRaw"
    # List[str] exception type names from except clauses
    # bare `except:` recorded as the sentinel "__bare__"

    # ── Function signature & behaviour ────────────────────────────────────────
    PARAMS_RAW = "sayou:paramsRaw"
    # List[dict] one entry per parameter:
    #   {name, kind, type_annotation, has_default}
    #   kind: POSITIONAL_ONLY | POSITIONAL_OR_KEYWORD |
    #         VAR_POSITIONAL | KEYWORD_ONLY | VAR_KEYWORD

    RETURN_TYPE = "sayou:returnType"
    # str | None — return annotation as dotted name
    # None = unannotated, "None" = explicitly annotated -> None

    IS_ASYNC = "sayou:isAsync"
    # bool — True when defined with `async def`

    IS_GENERATOR = "sayou:isGenerator"
    # bool — True when body contains yield / yield from

    INSTANCE_ATTRS_RAW = "sayou:instanceAttrsRaw"
    # List[str] self.<n> names assigned in __init__ — present on CLASS node
