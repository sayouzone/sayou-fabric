"""
Unit tests for LoaderPipeline.

Covers:
- _register_manual: type guard, name resolution
- _resolve_writer: explicit strategy, auto scoring, unknown → None
- run(): empty input, writer routing, error propagation
- process() facade
"""

import logging
from unittest.mock import patch

import pytest

from sayou.loader.core.exceptions import WriterError
from sayou.loader.pipeline import LoaderPipeline

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _bare_pipeline() -> LoaderPipeline:
    with patch.object(LoaderPipeline, "_register"), patch.object(
        LoaderPipeline, "_load_from_registry"
    ), patch.object(LoaderPipeline, "initialize"):
        p = LoaderPipeline.__new__(LoaderPipeline)
        p.writers_cls_map = {}
        p._callbacks = []
        p.global_config = {}
        p.logger = logging.getLogger("LoaderPipeline")
    return p


def _make_writer(name: str, score: float = 0.9):
    _score = score

    class _Writer:
        component_name = name
        _instance_ref = None

        @classmethod
        def can_handle(cls, data, destination, strategy="auto"):
            return _score

        def __init__(self):
            self.component_name = name
            self._callbacks: list = []
            self._write_called = False
            _Writer._instance_ref = self

        def add_callback(self, cb):
            self._callbacks.append(cb)

        def initialize(self, **kw):
            pass

        def write(self, data, destination, **kw):
            self._write_called = True
            return True

    _Writer.__name__ = name
    return _Writer


# ---------------------------------------------------------------------------
# _register_manual
# ---------------------------------------------------------------------------


class TestRegisterManual:
    def test_registers_by_component_name(self):
        p = _bare_pipeline()
        cls = _make_writer("FileWriter")
        p._register_manual(cls)
        assert "FileWriter" in p.writers_cls_map

    def test_non_type_raises_type_error(self):
        p = _bare_pipeline()
        with pytest.raises(TypeError):
            p._register_manual("not_a_class")

    def test_instance_raises_type_error(self):
        p = _bare_pipeline()
        cls = _make_writer("X")
        with pytest.raises(TypeError):
            p._register_manual(cls())


# ---------------------------------------------------------------------------
# _resolve_writer
# ---------------------------------------------------------------------------


class TestResolveWriter:
    def test_explicit_strategy_returns_match(self):
        p = _bare_pipeline()
        cls = _make_writer("FileWriter")
        p.writers_cls_map["FileWriter"] = cls
        assert p._resolve_writer([], "output.json", "FileWriter") is cls

    def test_auto_selects_highest_scorer(self):
        p = _bare_pipeline()
        low = _make_writer("Low", score=0.3)
        high = _make_writer("High", score=0.95)
        p.writers_cls_map = {"Low": low, "High": high}
        assert p._resolve_writer([], "dst", "auto") is high

    def test_returns_none_when_all_zero(self):
        p = _bare_pipeline()
        cls = _make_writer("Zero", score=0.0)
        p.writers_cls_map = {"Zero": cls}
        assert p._resolve_writer([], "dst", "auto") is None


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------


class TestRun:
    def test_empty_input_returns_true(self):
        p = _bare_pipeline()
        assert p.run(None, "output.json", strategy="auto") is True

    def test_empty_list_returns_true(self):
        p = _bare_pipeline()
        assert p.run([], "output.json", strategy="auto") is True

    def test_routing_calls_writer(self):
        p = _bare_pipeline()
        cls = _make_writer("File", score=0.9)
        p.writers_cls_map = {"File": cls}
        p.run({"data": "x"}, "out.json", strategy="auto")
        assert cls._instance_ref._write_called

    def test_raises_writer_error_when_no_writer(self):
        p = _bare_pipeline()
        with pytest.raises(WriterError):
            p.run({"data": "x"}, "out.json", strategy="auto")

    def test_explicit_strategy_bypasses_scoring(self):
        p = _bare_pipeline()
        low = _make_writer("Low", score=0.1)
        high = _make_writer("High", score=0.99)
        p.writers_cls_map = {"Low": low, "High": high}
        p.run({"data": "x"}, "out.json", strategy="Low")
        assert low._instance_ref._write_called
        assert high._instance_ref is None


# ---------------------------------------------------------------------------
# process() facade
# ---------------------------------------------------------------------------


class TestProcess:
    def test_process_facade_returns_bool(self):
        with patch.object(LoaderPipeline, "run", return_value=True) as mock_run:
            result = LoaderPipeline.process({"data": "x"}, "out.json", strategy="auto")
        mock_run.assert_called_once()
        assert result is True
