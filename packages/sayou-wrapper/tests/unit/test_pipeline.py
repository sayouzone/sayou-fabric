"""
Unit tests for WrapperPipeline.

Covers:
- _register_manual: type guard, name resolution
- _resolve_adapter: explicit strategy, auto scoring, unknown → None
- run(): empty input, adapter routing, callback propagation
- AdaptationError when no adapter found
"""

import logging
from unittest.mock import MagicMock, patch

import pytest
from sayou.core.schemas import SayouOutput

from sayou.wrapper.core.exceptions import AdaptationError
from sayou.wrapper.pipeline import WrapperPipeline

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _bare_pipeline(**kwargs) -> WrapperPipeline:
    """Instantiate WrapperPipeline with all discovery/init patched out."""
    with patch.object(WrapperPipeline, "_register"), patch.object(
        WrapperPipeline, "_load_from_registry"
    ), patch.object(WrapperPipeline, "initialize"):
        p = WrapperPipeline.__new__(WrapperPipeline)
        p.adapters_cls_map = {}
        p._callbacks = []
        p.global_config = {}
        p.logger = logging.getLogger("WrapperPipeline")
    return p


def _make_adapter(name: str, score: float = 0.9):
    """Return a real class whose instances are MagicMocks."""
    from unittest.mock import MagicMock as _MM

    _score = score
    _adapt_return = SayouOutput(nodes=[])

    class _Adapter:
        component_name = name
        _instance_ref = None  # shared across instances for assertion access

        @classmethod
        def can_handle(cls, data, strategy="auto"):
            return _score

        def __init__(self):
            self.component_name = name
            self._callbacks: list = []
            self._adapt = _MM(return_value=_adapt_return)
            _Adapter._instance_ref = self

        def add_callback(self, cb):
            self._callbacks.append(cb)

        def initialize(self, **kwargs):
            pass

        def adapt(self, data, **kwargs):
            return self._adapt(data, **kwargs)

    _Adapter.__name__ = name
    return _Adapter


# ---------------------------------------------------------------------------
# _register_manual
# ---------------------------------------------------------------------------


class TestRegisterManual:
    def test_registers_class_by_component_name(self):
        p = _bare_pipeline()
        cls = _make_adapter("MyAdapter")
        p._register_manual(cls)
        assert "MyAdapter" in p.adapters_cls_map

    def test_registers_class_by_dunder_name_fallback(self):
        p = _bare_pipeline()
        cls = _make_adapter("MyAdapter")
        del cls.component_name  # force fallback to __name__
        p._register_manual(cls)
        assert "MyAdapter" in p.adapters_cls_map

    def test_non_type_raises_type_error(self):
        p = _bare_pipeline()
        with pytest.raises(TypeError):
            p._register_manual("not_a_class")

    def test_instance_raises_type_error(self):
        p = _bare_pipeline()
        cls = _make_adapter("X")
        with pytest.raises(TypeError):
            p._register_manual(cls())  # pass instance instead of class


# ---------------------------------------------------------------------------
# _resolve_adapter
# ---------------------------------------------------------------------------


class TestResolveAdapter:
    def test_explicit_strategy_returns_exact_match(self):
        p = _bare_pipeline()
        cls = _make_adapter("document_chunk")
        p.adapters_cls_map["document_chunk"] = cls
        assert p._resolve_adapter([], "document_chunk") is cls

    def test_auto_selects_highest_scorer(self):
        p = _bare_pipeline()
        low = _make_adapter("Low", score=0.3)
        high = _make_adapter("High", score=0.95)
        p.adapters_cls_map = {"Low": low, "High": high}
        assert p._resolve_adapter([], "auto") is high

    def test_returns_none_when_all_zero(self):
        p = _bare_pipeline()
        cls = _make_adapter("Zero", score=0.0)
        p.adapters_cls_map = {"Zero": cls}
        assert p._resolve_adapter([], "auto") is None

    def test_unknown_explicit_strategy_falls_through_to_scoring(self):
        p = _bare_pipeline()
        cls = _make_adapter("Good", score=0.8)
        p.adapters_cls_map = {"Good": cls}
        # "unknown" is not in the map → scoring kicks in
        result = p._resolve_adapter([], "unknown")
        assert result is cls


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------


class TestRun:
    def test_empty_input_returns_empty_output(self):
        p = _bare_pipeline()
        result = p.run([], strategy="auto")
        assert isinstance(result, SayouOutput)
        assert result.nodes == []

    def test_none_input_returns_empty_output(self):
        p = _bare_pipeline()
        result = p.run(None, strategy="auto")
        assert result.nodes == []

    def test_routing_calls_adapter(self):
        p = _bare_pipeline()
        cls = _make_adapter("Doc", score=0.9)
        p.adapters_cls_map = {"Doc": cls}

        result = p.run([{"content": "hello"}], strategy="auto")
        cls._instance_ref._adapt.assert_called_once()
        assert isinstance(result, SayouOutput)

    def test_raises_adaptation_error_when_no_adapter(self):
        p = _bare_pipeline()
        # No adapters registered
        with pytest.raises(AdaptationError):
            p.run([{"content": "x"}], strategy="auto")

    def test_callbacks_forwarded_to_adapter(self):
        p = _bare_pipeline()
        cb = MagicMock()
        p._callbacks = [cb]
        cls = _make_adapter("Doc", score=0.9)
        p.adapters_cls_map = {"Doc": cls}

        p.run([{"content": "x"}], strategy="auto")
        assert cb in cls._instance_ref._callbacks

    def test_explicit_strategy_bypasses_scoring(self):
        p = _bare_pipeline()
        low = _make_adapter("Low", score=0.1)
        high = _make_adapter("High", score=0.99)
        p.adapters_cls_map = {"Low": low, "High": high}

        p.run([{"content": "x"}], strategy="Low")
        # Low should be called even though High scores higher
        low._instance_ref._adapt.assert_called_once()
        assert high._instance_ref is None


# ---------------------------------------------------------------------------
# process() facade
# ---------------------------------------------------------------------------


class TestProcess:
    def test_process_creates_instance_and_runs(self):
        with patch.object(
            WrapperPipeline, "run", return_value=SayouOutput(nodes=[])
        ) as mock_run:
            result = WrapperPipeline.process([{"content": "x"}], strategy="auto")
        mock_run.assert_called_once()
        assert isinstance(result, SayouOutput)
