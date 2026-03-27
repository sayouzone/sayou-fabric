"""
conftest.py for sayou-document tests.

Expected monorepo layout
------------------------
    sayou-fabric/
    └── packages/
        ├── sayou-core/        └── src/sayou/core/
        ├── sayou-document/    └── src/sayou/document/   ← this package
        ├── sayou-refinery/    └── src/sayou/refinery/
        └── ...

Run from sayou-document/:

    cd packages/sayou-document
    pytest

What this file does
-------------------
1. Finds every packages/*/src/ directory and adds it to sys.path.
2. Builds a ``sayou`` namespace package whose __path__ covers all of them,
   so ``from sayou.document.xxx import …`` and ``from sayou.core.xxx import …``
   both resolve correctly.
3. Stubs ``sayou.core.*`` if sayou-core is not yet on sys.path.
4. Stubs optional heavy dependencies only when genuinely absent.
"""

from __future__ import annotations

import importlib.util
import logging
import sys
import types
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# 0. Locate every packages/*/src/ in the monorepo and add to sys.path
#
#    __file__ = .../packages/sayou-document/tests/conftest.py
#    parent        = .../packages/sayou-document/tests/
#    parent.parent = .../packages/sayou-document/        ← this package root
#    parent.parent.parent = .../packages/               ← all packages live here
# ---------------------------------------------------------------------------
_THIS_PKG = Path(__file__).resolve().parent.parent  # sayou-document/
_PACKAGES = _THIS_PKG.parent  # packages/

_src_dirs: List[Path] = []

for _pkg_dir in sorted(_PACKAGES.iterdir()):
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
# 2. sayou.core stubs (used when sayou-core is not installed)
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
        def decorator(fn):
            def wrapper(self, *args, **kwargs):
                try:
                    return fn(self, *args, **kwargs)
                except:
                    return default_return

            wrapper.__name__ = fn.__name__
            return wrapper

        return decorator

    def measure_time(fn):
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        wrapper.__name__ = fn.__name__
        return wrapper

    _dec.safe_run = safe_run
    _dec.measure_time = measure_time
    sys.modules["sayou.core.decorators"] = _dec

    _reg = types.ModuleType("sayou.core.registry")
    COMPONENT_REGISTRY: Dict[str, Dict] = {}

    def register_component(kind: str):
        def decorator(cls):
            COMPONENT_REGISTRY.setdefault(kind, {})[
                getattr(cls, "component_name", cls.__name__)
            ] = cls
            return cls

        return decorator

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
# 3. Optional dependency stubs (only when genuinely absent)
# ---------------------------------------------------------------------------
def _stub_if_missing(name: str) -> None:
    if importlib.util.find_spec(name) is None and name not in sys.modules:
        sys.modules[name] = MagicMock()


_stub_if_missing("fitz")
_stub_if_missing("PIL")
_stub_if_missing("PIL.Image")
_stub_if_missing("openpyxl")
_stub_if_missing("openpyxl.drawing")
_stub_if_missing("openpyxl.drawing.image")
_stub_if_missing("pytesseract")
_stub_if_missing("chardet")

_stub_if_missing("pptx")
_stub_if_missing("pptx.util")
_stub_if_missing("pptx.enum.text")
if importlib.util.find_spec("pptx") is None:
    _mso = types.ModuleType("pptx.enum.shapes")

    class _MSO:
        GROUP = 6
        PICTURE = 13
        TABLE = 19
        CHART = 3
        TEXT_BOX = 17

    _mso.MSO_SHAPE_TYPE = _MSO
    sys.modules["pptx.enum.shapes"] = _mso

_stub_if_missing("docx")
_stub_if_missing("docx.oxml")
_stub_if_missing("docx.oxml.ns")
_stub_if_missing("docx.table")
_stub_if_missing("docx.text")
_stub_if_missing("docx.text.paragraph")
if importlib.util.find_spec("docx") is None:
    _wds = types.ModuleType("docx.enum.style")

    class _WDS:
        PARAGRAPH = "PARAGRAPH"
        CHARACTER = "CHARACTER"

    _wds.WD_STYLE_TYPE = _WDS
    sys.modules["docx.enum.style"] = _wds
