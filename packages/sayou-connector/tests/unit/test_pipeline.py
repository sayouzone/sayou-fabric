"""
Unit tests for ConnectorPipeline.

Covers:
- _register_manual: generator class, fetcher class, instance guard (TypeError)
- _resolve_generator: explicit strategy, auto detection, unknown strategy (ValueError)
- run(): bad strategy name raises ValueError
- run(): task with unknown source_type is skipped (logged, not raised)
- Callback propagation (hasattr guard — no AttributeError without _callbacks)
"""

from typing import Iterator
from unittest.mock import MagicMock, patch

import pytest
from sayou.connector.interfaces.base_fetcher import BaseFetcher
from sayou.connector.interfaces.base_generator import BaseGenerator
from sayou.connector.pipeline import ConnectorPipeline
from sayou.core.registry import register_component
from sayou.core.schemas import SayouPacket, SayouTask

# ---------------------------------------------------------------------------
# Minimal stubs (not registered globally — registered via extra_* params)
# ---------------------------------------------------------------------------


class StubGenerator(BaseGenerator):
    component_name = "StubGenerator"
    SUPPORTED_TYPES = ["stub"]

    @classmethod
    def can_handle(cls, source: str) -> float:
        return 1.0 if source == "stub://" else 0.0

    def initialize(self, source: str, **kwargs):
        self._items = kwargs.get("items", [])

    def _do_generate(self, source: str, **kwargs) -> Iterator[SayouTask]:
        for item in self._items:
            yield SayouTask(source_type="stub", uri=item, params={}, meta={})


class StubFetcher(BaseFetcher):
    component_name = "StubFetcher"
    SUPPORTED_TYPES = ["stub"]
    FETCH_MAX_RETRIES = 1  # no retry in unit tests

    def _do_fetch(self, task: SayouTask):
        return f"data:{task.uri}"


# ---------------------------------------------------------------------------
# _register_manual guard
# ---------------------------------------------------------------------------


class TestRegisterManual:
    def test_instance_instead_of_generator_class_raises(self):
        with pytest.raises(TypeError, match="CLASS"):
            ConnectorPipeline(extra_generators=[StubGenerator()])

    def test_instance_instead_of_fetcher_class_raises(self):
        with pytest.raises(TypeError, match="CLASS"):
            ConnectorPipeline(extra_fetchers=[StubFetcher()])

    def test_valid_generator_class_registers(self):
        p = ConnectorPipeline(extra_generators=[StubGenerator])
        assert "StubGenerator" in p.generator_cls_map or "stub" in p.generator_cls_map

    def test_valid_fetcher_class_registers(self):
        p = ConnectorPipeline(extra_fetchers=[StubFetcher])
        # _register_manual stores fetcher instances keyed by component_name.
        # SUPPORTED_TYPES-based keys are only added by _load_from_registry
        # (for fetchers coming from the global registry, not extra_fetchers).
        assert "StubFetcher" in p.fetcher_cls_map


# ---------------------------------------------------------------------------
# _resolve_generator
# ---------------------------------------------------------------------------


class TestResolveGenerator:
    def test_explicit_file_strategy_resolves(self):
        p = ConnectorPipeline()
        cls = p._resolve_generator(".", "file")
        assert cls.component_name == "FileGenerator"

    def test_unknown_strategy_raises_value_error(self):
        p = ConnectorPipeline()
        with pytest.raises(ValueError, match="unknown_strategy"):
            p._resolve_generator(".", "unknown_strategy")

    def test_auto_detects_sqlite_source(self):
        p = ConnectorPipeline()
        cls = p._resolve_generator("sqlite:///test.db", "auto")
        assert "sqlite" in cls.component_name.lower() or cls.SUPPORTED_TYPES == [
            "sqlite"
        ]

    def test_auto_detects_http_source(self):
        p = ConnectorPipeline()
        cls = p._resolve_generator("https://example.com", "auto")
        assert (
            "request" in cls.component_name.lower() or "requests" in cls.SUPPORTED_TYPES
        )


# ---------------------------------------------------------------------------
# run() — bad strategy
# ---------------------------------------------------------------------------


class TestRunBadStrategy:
    def test_unknown_strategy_name_raises(self):
        p = ConnectorPipeline()
        with pytest.raises(ValueError):
            list(p.run(source=".", strategy="__no_such_strategy__"))


# ---------------------------------------------------------------------------
# run() — unknown source_type is skipped, not raised
# ---------------------------------------------------------------------------


class TestRunUnknownSourceType:
    def test_task_with_unknown_source_type_skipped(self):
        """Tasks whose source_type has no registered fetcher must be silently skipped."""

        class OrphanGenerator(BaseGenerator):
            component_name = "OrphanGenerator"
            SUPPORTED_TYPES = ["orphan"]

            @classmethod
            def can_handle(cls, source):
                return 0.0

            def initialize(self, source, **kwargs):
                pass

            def _do_generate(self, source, **kwargs):
                yield SayouTask(
                    source_type="__no_fetcher__", uri="x", params={}, meta={}
                )

        p = ConnectorPipeline(extra_generators=[OrphanGenerator])
        # Providing strategy explicitly to avoid auto-detection noise
        p.generator_cls_map["orphan"] = OrphanGenerator

        # Should return an empty iterator, not raise
        results = list(p.run(source=".", strategy="orphan"))
        assert results == []


# ---------------------------------------------------------------------------
# _callbacks guard — no AttributeError when _callbacks is absent
# ---------------------------------------------------------------------------


class TestCallbacksGuard:
    def test_run_with_no_registered_callbacks_does_not_raise(self):
        """
        BaseComponent initialises _callbacks=[] in __init__, so the attribute
        always exists.  What matters is that run() completes without error when
        no callbacks have been registered (i.e., _callbacks is an empty list).
        """
        p = ConnectorPipeline(
            extra_generators=[StubGenerator], extra_fetchers=[StubFetcher]
        )
        assert p._callbacks == []  # empty, not absent
        p.generator_cls_map["stub"] = StubGenerator
        results = list(p.run(source="stub://", strategy="stub", items=[]))
        assert results == []
