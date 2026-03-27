"""
Unit tests for AssemblerPipeline.

Covers:
- _register_manual: type guard, name resolution
- _resolve_builder: explicit strategy, auto scoring, unknown → None
- run(): empty input, builder routing, callback propagation
- BuildError when no builder found
"""

import logging
from unittest.mock import patch

import pytest
from sayou.core.schemas import SayouOutput

from sayou.assembler.core.exceptions import BuildError
from sayou.assembler.pipeline import AssemblerPipeline

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _bare_pipeline() -> AssemblerPipeline:
    with patch.object(AssemblerPipeline, "_register"), patch.object(
        AssemblerPipeline, "_load_from_registry"
    ), patch.object(AssemblerPipeline, "initialize"):
        p = AssemblerPipeline.__new__(AssemblerPipeline)
        p.builders_cls_map = {}
        p._callbacks = []
        p.global_config = {}
        p.logger = logging.getLogger("AssemblerPipeline")
    return p


def _make_builder(name: str, score: float = 0.9):
    _score = score
    _build_return = {"nodes": [], "edges": []}

    class _Builder:
        component_name = name
        _instance_ref = None

        @classmethod
        def can_handle(cls, data, strategy="auto"):
            return _score

        def __init__(self):
            self.component_name = name
            self._callbacks: list = []
            self._build_called = False
            _Builder._instance_ref = self

        def add_callback(self, cb):
            self._callbacks.append(cb)

        def initialize(self, **kw):
            pass

        def build(self, data, **kw):
            self._build_called = True
            return _build_return

    _Builder.__name__ = name
    return _Builder


def _output(*node_ids):
    from sayou.core.schemas import SayouNode

    return SayouOutput(
        nodes=[SayouNode(node_id=nid, node_class="Node") for nid in node_ids]
    )


# ---------------------------------------------------------------------------
# _register_manual
# ---------------------------------------------------------------------------


class TestRegisterManual:
    def test_registers_by_component_name(self):
        p = _bare_pipeline()
        cls = _make_builder("GraphBuilder")
        p._register_manual(cls)
        assert "GraphBuilder" in p.builders_cls_map

    def test_non_type_raises_type_error(self):
        p = _bare_pipeline()
        with pytest.raises(TypeError):
            p._register_manual("not_a_class")

    def test_instance_raises_type_error(self):
        p = _bare_pipeline()
        cls = _make_builder("X")
        with pytest.raises(TypeError):
            p._register_manual(cls())


# ---------------------------------------------------------------------------
# _resolve_builder
# ---------------------------------------------------------------------------


class TestResolveBuilder:
    def test_explicit_strategy_returns_exact_match(self):
        p = _bare_pipeline()
        cls = _make_builder("graph")
        p.builders_cls_map["graph"] = cls
        assert p._resolve_builder(_output("n1"), "graph") is cls

    def test_auto_selects_highest_score(self):
        p = _bare_pipeline()
        low = _make_builder("Low", score=0.3)
        high = _make_builder("High", score=0.95)
        p.builders_cls_map = {"Low": low, "High": high}
        assert p._resolve_builder(_output("n1"), "auto") is high

    def test_returns_none_when_all_zero(self):
        p = _bare_pipeline()
        cls = _make_builder("Zero", score=0.0)
        p.builders_cls_map = {"Zero": cls}
        assert p._resolve_builder(_output("n1"), "auto") is None

    def test_unknown_explicit_falls_to_scoring(self):
        p = _bare_pipeline()
        cls = _make_builder("Good", score=0.8)
        p.builders_cls_map = {"Good": cls}
        assert p._resolve_builder(_output("n1"), "unknown") is cls


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------


class TestRun:
    def test_empty_input_returns_empty_list(self):
        p = _bare_pipeline()
        assert p.run(None, strategy="graph") == []

    def test_empty_list_returns_empty(self):
        p = _bare_pipeline()
        assert p.run([], strategy="graph") == []

    def test_routing_calls_builder(self):
        p = _bare_pipeline()
        cls = _make_builder("Graph", score=0.9)
        p.builders_cls_map = {"Graph": cls}
        result = p.run(_output("n1"), strategy="auto")
        assert cls._instance_ref._build_called

    def test_raises_build_error_when_no_builder(self):
        p = _bare_pipeline()
        with pytest.raises(BuildError):
            p.run(_output("n1"), strategy="auto")

    def test_callbacks_forwarded(self):
        p = _bare_pipeline()
        cb = lambda e: None
        p._callbacks = [cb]
        cls = _make_builder("Graph", score=0.9)
        p.builders_cls_map = {"Graph": cls}
        p.run(_output("n1"), strategy="auto")
        assert cb in cls._instance_ref._callbacks

    def test_explicit_strategy_bypasses_scoring(self):
        p = _bare_pipeline()
        low = _make_builder("Low", score=0.1)
        high = _make_builder("High", score=0.99)
        p.builders_cls_map = {"Low": low, "High": high}
        p.run(_output("n1"), strategy="Low")
        assert low._instance_ref._build_called
        assert high._instance_ref is None


# ---------------------------------------------------------------------------
# process() facade
# ---------------------------------------------------------------------------


class TestProcess:
    def test_process_facade(self):
        with patch.object(AssemblerPipeline, "run", return_value=[]) as mock_run:
            AssemblerPipeline.process(_output("n1"), strategy="graph")
        mock_run.assert_called_once()
