"""
conftest.py for sayou-wrapper tests.

Extends the root conftest with:
- SayouNode / SayouOutput schemas
- sayou.core.ontology stubs (SayouClass, SayouAttribute, SayouPredicate)
"""

from __future__ import annotations

import importlib.util
import logging
import sys
import types
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# 0. sys.path — add every packages/*/src/
# ---------------------------------------------------------------------------
_REPO = Path(__file__).resolve().parent.parent.parent  # /home/claude

_src_dirs: List[Path] = []
for _pkg_dir in sorted(_REPO.iterdir()):
    if not _pkg_dir.is_dir() or _pkg_dir.name.startswith("."):
        continue
    _src = _pkg_dir / "src"
    if _src.is_dir():
        _src_dirs.append(_src)
        if str(_src) not in sys.path:
            sys.path.insert(0, str(_src))

# ---------------------------------------------------------------------------
# 1. sayou namespace package
# ---------------------------------------------------------------------------
if "sayou" not in sys.modules:
    _sayou = types.ModuleType("sayou")
    _sayou.__path__ = [
        str(_src / "sayou") for _src in _src_dirs if (_src / "sayou").is_dir()
    ]
    sys.modules["sayou"] = _sayou
else:
    _sayou = sys.modules["sayou"]
    for _src in _src_dirs:
        _p = str(_src / "sayou")
        if (_src / "sayou").is_dir() and _p not in list(
            getattr(_sayou, "__path__", [])
        ):
            _sayou.__path__.append(_p)

# ---------------------------------------------------------------------------
# 2. sayou.core stubs
# ---------------------------------------------------------------------------
if "sayou.core" not in sys.modules:
    from pydantic import BaseModel as _BM
    from pydantic import ConfigDict as _CD

    _exc = types.ModuleType("sayou.core.exceptions")

    class SayouCoreError(Exception):
        pass

    _exc.SayouCoreError = SayouCoreError
    sys.modules["sayou.core.exceptions"] = _exc

    _schemas = types.ModuleType("sayou.core.schemas")

    class SayouBlock(_BM):
        model_config = _CD(extra="allow")
        type: str
        content: Any = None
        metadata: Dict = {}

    class SayouChunk(_BM):
        model_config = _CD(extra="allow")
        content: str = ""
        metadata: Dict = {}

    class SayouNode(_BM):
        model_config = _CD(extra="allow")
        node_id: str
        node_class: str = "Node"
        friendly_name: str = ""
        attributes: Dict = {}
        relationships: Dict = {}

    class SayouOutput(_BM):
        model_config = _CD(extra="allow")
        nodes: List[SayouNode] = []
        metadata: Dict = {}

    class SayouTask(_BM):
        model_config = _CD(extra="allow")
        uri: str = ""
        source_type: str = ""
        params: Dict = {}
        meta: Dict = {}

    class SayouPacket(_BM):
        model_config = _CD(extra="allow")
        data: Any = None
        metadata: Dict = {}

    _schemas.SayouBlock = SayouBlock
    _schemas.SayouChunk = SayouChunk
    _schemas.SayouNode = SayouNode
    _schemas.SayouOutput = SayouOutput
    _schemas.SayouTask = SayouTask
    _schemas.SayouPacket = SayouPacket
    sys.modules["sayou.core.schemas"] = _schemas

    _bc = types.ModuleType("sayou.core.base_component")

    class BaseComponent:
        component_name: str = "BaseComponent"

        def __init__(self):
            self.logger = logging.getLogger(self.__class__.__name__)
            self._callbacks: List = []
            self.config: Dict = {}

        def _log(self, msg: str, level: str = "info") -> None:
            pass

        def _emit(self, event: str, **kwargs) -> None:
            pass

        def initialize(self, **kwargs) -> None:
            pass

        def add_callback(self, cb) -> None:
            self._callbacks.append(cb)

    _bc.BaseComponent = BaseComponent
    sys.modules["sayou.core.base_component"] = _bc

    _dec = types.ModuleType("sayou.core.decorators")

    def safe_run(default_return=None):
        def d(fn):
            def w(self, *a, **k):
                try:
                    return fn(self, *a, **k)
                except:
                    return default_return

            w.__name__ = fn.__name__
            return w

        return d

    def measure_time(fn):
        def w(*a, **k):
            return fn(*a, **k)

        w.__name__ = fn.__name__
        return w

    def retry(max_retries=3, delay=1.0):
        """Stub: no-op retry decorator for tests."""

        def decorator(fn):
            def wrapper(*a, **k):
                return fn(*a, **k)

            wrapper.__name__ = fn.__name__
            return wrapper

        return decorator

    _dec.retry = retry
    _dec.safe_run = safe_run
    _dec.measure_time = measure_time
    sys.modules["sayou.core.decorators"] = _dec

    _reg = types.ModuleType("sayou.core.registry")
    COMPONENT_REGISTRY: Dict[str, Dict] = {}

    def register_component(kind: str):
        def d(cls):
            COMPONENT_REGISTRY.setdefault(kind, {})[
                getattr(cls, "component_name", cls.__name__)
            ] = cls
            return cls

        return d

    _reg.COMPONENT_REGISTRY = COMPONENT_REGISTRY
    _reg.register_component = register_component
    sys.modules["sayou.core.registry"] = _reg

    _core = types.ModuleType("sayou.core")
    _core.exceptions = _exc
    _core.schemas = _schemas
    _core.base_component = _bc
    _core.decorators = _dec
    _core.registry = _reg
    sys.modules["sayou.core"] = _core
    _sayou.core = _core

# ---------------------------------------------------------------------------
# 3. sayou.core.ontology stub
# ---------------------------------------------------------------------------
if "sayou.core.ontology" not in sys.modules:
    _onto = types.ModuleType("sayou.core.ontology")

    class SayouClass:
        TEXT = "sayou:TextFragment"
        TOPIC = "sayou:Topic"
        TABLE = "sayou:Table"
        CODE_BLOCK = "sayou:CodeBlock"
        LIST_ITEM = "sayou:ListItem"
        FILE = "sayou:File"
        CLASS = "sayou:Class"
        METHOD = "sayou:Method"
        FUNCTION = "sayou:Function"
        ATTRIBUTE_BLOCK = "sayou:AttributeBlock"
        VIDEO = "sayou:Video"
        VIDEO_SEGMENT = "sayou:VideoSegment"

    class SayouAttribute:
        TEXT = "schema:text"
        SEMANTIC_TYPE = "sayou:semanticType"
        PAGE_INDEX = "sayou:pageIndex"
        PART_INDEX = "sayou:partIndex"
        SOURCE = "sayou:source"
        FILE_PATH = "sayou:filePath"
        LANGUAGE = "sayou:language"
        SYMBOL_NAME = "sayou:symbolName"
        PARENT_CLASS = "sayou:parentClass"
        LINE_START = "sayou:lineStart"
        LINE_END = "sayou:lineEnd"
        INHERITS_FROM_RAW = "sayou:inheritsFromRaw"
        DECORATORS_RAW = "sayou:decoratorsRaw"
        INSTANCE_ATTRS_RAW = "sayou:instanceAttrsRaw"
        CALLS_RAW = "sayou:callsRaw"
        ATTR_CALLS_RAW = "sayou:attrCallsRaw"
        TYPE_REFS_RAW = "sayou:typeRefsRaw"
        GLOBALS_DECLARED_RAW = "sayou:globalsDeclaredRaw"
        RAISES_RAW = "sayou:raisesRaw"
        CATCHES_RAW = "sayou:catchesRaw"
        PARAMS_RAW = "sayou:paramsRaw"
        IS_ASYNC = "sayou:isAsync"
        IS_GENERATOR = "sayou:isGenerator"
        RETURN_TYPE = "sayou:returnType"
        MODULE_ALL_RAW = "sayou:moduleAllRaw"
        MODULE_VARS_RAW = "sayou:moduleVarsRaw"
        START_TIME = "sayou:startTime"
        END_TIME = "sayou:endTime"

    class SayouPredicate:
        HAS_PARENT = "sayou:hasParent"
        CONTAINS = "sayou:contains"
        DEFINED_IN = "sayou:definedIn"
        CALLS = "sayou:calls"
        MAYBE_CALLS = "sayou:maybeCalls"
        INHERITS = "sayou:inherits"
        OVERRIDES = "sayou:overrides"
        USES_TYPE = "sayou:usesType"
        MUTATES_GLOBAL = "sayou:mutatesGlobal"
        RAISES = "sayou:raises"
        EXPOSES = "sayou:exposes"
        IMPORTS = "sayou:imports"
        NEXT = "sayou:next"

    class SayouEdgeMeta:
        CONFIDENCE = "confidence"
        RESOLUTION = "resolution"
        EDGE_SOURCE = "edge_source"

    _onto.SayouClass = SayouClass
    _onto.SayouAttribute = SayouAttribute
    _onto.SayouPredicate = SayouPredicate
    _onto.SayouEdgeMeta = SayouEdgeMeta
    sys.modules["sayou.core.ontology"] = _onto
    sys.modules["sayou.core"].ontology = _onto
