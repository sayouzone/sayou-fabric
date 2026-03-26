"""
Unit tests for BaseFetcher retry logic.

The retry behaviour is now controlled by class attributes
FETCH_MAX_RETRIES and FETCH_RETRY_DELAY, making it fully testable
without mocking decorators.

Covers:
- Success on the first attempt → no retry, returns SayouPacket(success=True).
- Transient failure then success → retries and eventually succeeds.
- Permanent failure → after FETCH_MAX_RETRIES attempts returns SayouPacket(success=False).
- FETCH_MAX_RETRIES=1 disables retrying (one attempt only).
- Returned packet always has the original task attached.
- FETCH_RETRY_DELAY is respected (mocked via sleep).
"""

from unittest.mock import MagicMock, call, patch

import pytest
from sayou.core.schemas import SayouPacket, SayouTask

from sayou.connector.interfaces.base_fetcher import BaseFetcher

# ---------------------------------------------------------------------------
# Concrete stub fetcher
# ---------------------------------------------------------------------------


class CountingFetcher(BaseFetcher):
    """Fails for the first `fail_times` calls, then succeeds."""

    component_name = "CountingFetcher"
    SUPPORTED_TYPES = ["test"]
    FETCH_MAX_RETRIES = 3
    FETCH_RETRY_DELAY = 0.0  # no sleep in tests

    def __init__(self, fail_times: int = 0, return_value=b"ok"):
        super().__init__()
        self._fail_times = fail_times
        self._call_count = 0
        self._return_value = return_value

    def _do_fetch(self, task: SayouTask):
        self._call_count += 1
        if self._call_count <= self._fail_times:
            raise ConnectionError(f"Simulated failure #{self._call_count}")
        return self._return_value


def _task() -> SayouTask:
    return SayouTask(source_type="test", uri="test://resource", params={}, meta={})


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestBaseFetcherRetry:
    def test_success_on_first_attempt(self):
        fetcher = CountingFetcher(fail_times=0)
        packet = fetcher.fetch(_task())

        assert packet.success is True
        assert packet.data == b"ok"
        assert fetcher._call_count == 1

    def test_retry_on_transient_failure_then_success(self):
        fetcher = CountingFetcher(fail_times=2, return_value=b"recovered")
        packet = fetcher.fetch(_task())

        assert packet.success is True
        assert packet.data == b"recovered"
        assert fetcher._call_count == 3  # 2 failures + 1 success

    def test_permanent_failure_returns_failed_packet(self):
        fetcher = CountingFetcher(fail_times=99)  # always fails
        packet = fetcher.fetch(_task())

        assert packet.success is False
        assert packet.data is None
        assert packet.error is not None
        assert fetcher._call_count == fetcher.FETCH_MAX_RETRIES

    def test_max_retries_one_means_no_retry(self):
        class SingleShotFetcher(CountingFetcher):
            FETCH_MAX_RETRIES = 1

        fetcher = SingleShotFetcher(fail_times=99)
        packet = fetcher.fetch(_task())

        assert packet.success is False
        assert fetcher._call_count == 1

    def test_task_attached_to_packet_on_success(self):
        fetcher = CountingFetcher(fail_times=0)
        task = _task()
        packet = fetcher.fetch(task)
        assert packet.task is task

    def test_task_attached_to_packet_on_failure(self):
        fetcher = CountingFetcher(fail_times=99)
        task = _task()
        packet = fetcher.fetch(task)
        assert packet.task is task

    def test_retry_delay_called_between_attempts(self):
        """sleep() should be called exactly (max_retries - 1) times on permanent failure."""
        fetcher = CountingFetcher(fail_times=99)
        fetcher.FETCH_RETRY_DELAY = 1.0  # non-zero so the call matters

        with patch("sayou.connector.interfaces.base_fetcher.sleep") as mock_sleep:
            fetcher.fetch(_task())
            expected_calls = fetcher.FETCH_MAX_RETRIES - 1
            assert mock_sleep.call_count == expected_calls

    def test_subclass_can_override_max_retries(self):
        class HighRetryFetcher(CountingFetcher):
            FETCH_MAX_RETRIES = 5

        fetcher = HighRetryFetcher(fail_times=99)
        fetcher.fetch(_task())
        assert fetcher._call_count == 5

    def test_error_message_includes_component_name(self):
        fetcher = CountingFetcher(fail_times=99)
        packet = fetcher.fetch(_task())
        assert "CountingFetcher" in packet.error
