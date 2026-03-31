"""
conftest.py for sayou-brain tests.

Stubs all sub-library pipelines so Brain can be tested in isolation
without installing the full Sayou Fabric stack.
"""

from __future__ import annotations

import logging
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# sys.path — brain src
# ---------------------------------------------------------------------------
_BRAIN_SRC = Path(__file__).resolve().parent.parent.parent / "brain_pkg" / "src"
if str(_BRAIN_SRC) not in sys.path:
    sys.path.insert(0, str(_BRAIN_SRC))

# Register brain under sayou namespace
import importlib
import types as _types

if "sayou.brain" not in sys.modules:
    _brain_ns = _types.ModuleType("sayou.brain")
    _brain_ns.__path__ = [str(_BRAIN_SRC / "sayou" / "brain")]
    sys.modules["sayou.brain"] = _brain_ns
    if "sayou" in sys.modules:
        sys.modules["sayou"].brain = _brain_ns

_CORE_SRC = Path(__file__).resolve().parent.parent.parent / "core_pkg" / "src"
if str(_CORE_SRC) not in sys.path:
    sys.path.insert(0, str(_CORE_SRC))

# ---------------------------------------------------------------------------
# sayou namespace
# ---------------------------------------------------------------------------
if "sayou" not in sys.modules:
    _sayou = types.ModuleType("sayou")
    _sayou.__path__ = []
    sys.modules["sayou"] = _sayou
else:
    _sayou = sys.modules["sayou"]

# ---------------------------------------------------------------------------
# Core stubs (minimal — only what Brain needs)
# ---------------------------------------------------------------------------
if "sayou.core" not in sys.modules:
    from pydantic import BaseModel, ConfigDict

    _exc = types.ModuleType("sayou.core.exceptions")

    class SayouCoreError(Exception):
        pass

    _exc.SayouCoreError = SayouCoreError
    sys.modules["sayou.core.exceptions"] = _exc

    _schemas = types.ModuleType("sayou.core.schemas")

    class SayouPacket(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        data: object = None
        success: bool = True
        error: str | None = None
        meta: dict = {}
        task: object = None

    class SayouOutput(BaseModel):
        nodes: list = []
        metadata: dict = {}

    class SayouBlock(BaseModel):
        type: str = "text"
        content: object = ""
        metadata: dict = {}

    class SayouNode(BaseModel):
        node_id: str = "node"
        node_class: str = "Node"
        friendly_name: str = ""
        attributes: dict = {}
        relationships: dict = {}
        vector: list | None = None

    _schemas.SayouPacket = SayouPacket
    _schemas.SayouOutput = SayouOutput
    _schemas.SayouBlock = SayouBlock
    _schemas.SayouNode = SayouNode
    sys.modules["sayou.core.schemas"] = _schemas

    _bc = types.ModuleType("sayou.core.base_component")

    class BaseComponent:
        component_name = "BaseComponent"

        def __init__(self):
            self.logger = logging.getLogger(self.__class__.__name__)
            if not self.logger.handlers:
                self.logger.addHandler(logging.NullHandler())
            self._callbacks = []

        def _log(self, msg, level="info"):
            pass

        def _emit(self, event, **kw):
            pass

        def initialize(self, **kw):
            pass

        def add_callback(self, cb):
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

    _dec.safe_run = safe_run
    _dec.measure_time = measure_time
    sys.modules["sayou.core.decorators"] = _dec

    _core_cfg = types.ModuleType("sayou.core.config")

    class SayouConfig:
        def __init__(self, d=None):
            self._config = d or {}

        def get(self, section, key=None, default=None):
            s = self._config.get(section, {})
            if key is None:
                return s
            return s.get(key, default)

        def section(self, name):
            return self._config.get(name, {})

        def set(self, section, key, value):
            self._config.setdefault(section, {})[key] = value

        def merge(self, other):
            merged = {}
            for s in set(self._config) | set(other._config):
                merged[s] = {**self._config.get(s, {}), **other._config.get(s, {})}
            return SayouConfig(merged)

    _core_cfg.SayouConfig = SayouConfig
    sys.modules["sayou.core.config"] = _core_cfg

    _core = types.ModuleType("sayou.core")
    for _name, _mod in [
        ("exceptions", _exc),
        ("schemas", _schemas),
        ("base_component", _bc),
        ("decorators", _dec),
        ("config", _core_cfg),
    ]:
        setattr(_core, _name, _mod)
    sys.modules["sayou.core"] = _core
    _sayou.core = _core


# ---------------------------------------------------------------------------
# Sub-library pipeline stubs
# ---------------------------------------------------------------------------
def _make_pipeline_stub(module_name: str, class_name: str):
    mod = types.ModuleType(module_name)
    mock_cls = MagicMock()
    mock_instance = MagicMock()
    mock_instance._callbacks = []
    mock_instance.add_callback = lambda cb: mock_instance._callbacks.append(cb)
    mock_instance.initialize = MagicMock(return_value=None)
    mock_instance.run = MagicMock(return_value=None)
    mock_cls.return_value = mock_instance
    setattr(mod, class_name, mock_cls)
    sys.modules[module_name] = mod
    return mock_cls, mock_instance


for _lib, _cls in [
    ("sayou.connector", "ConnectorPipeline"),
    ("sayou.document", "DocumentPipeline"),
    ("sayou.refinery", "RefineryPipeline"),
    ("sayou.chunking", "ChunkingPipeline"),
    ("sayou.wrapper", "WrapperPipeline"),
    ("sayou.assembler", "AssemblerPipeline"),
    ("sayou.loader", "LoaderPipeline"),
]:
    _make_pipeline_stub(_lib, _cls)
