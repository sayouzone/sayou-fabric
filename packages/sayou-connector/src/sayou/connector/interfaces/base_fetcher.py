from abc import abstractmethod
from time import sleep
from typing import Any

from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time
from sayou.core.schemas import SayouPacket, SayouTask

from ..core.exceptions import FetcherError


class BaseFetcher(BaseComponent):
    """
    (Tier 1) Abstract base class for all data fetchers.

    This class implements the Template Method pattern. It handles common logic
    like logging, error wrapping, and retries in ``fetch()``, while delegating
    the actual retrieval logic to ``_do_fetch()``.

    Retry behaviour is controlled by two class-level attributes that concrete
    fetchers (or their callers) can override without touching this base class:

    Attributes:
        FETCH_MAX_RETRIES (int): Maximum number of fetch attempts (default: 3).
            Set to 1 to disable retries.
        FETCH_RETRY_DELAY (float): Seconds to wait between retries (default: 1.0).
    """

    component_name = "BaseFetcher"
    SUPPORTED_TYPES = []

    FETCH_MAX_RETRIES: int = 3
    FETCH_RETRY_DELAY: float = 1.0

    @classmethod
    def can_handle(cls, uri: str) -> float:
        """
        Evaluates whether this fetcher can handle the specific Task URI.
        """
        return 0.0

    @measure_time
    def fetch(self, task: SayouTask) -> SayouPacket:
        """
        Execute the fetching process for a given task.

        Retries up to ``FETCH_MAX_RETRIES`` times on transient errors, waiting
        ``FETCH_RETRY_DELAY`` seconds between attempts. Always returns a
        ``SayouPacket``; never raises.

        Args:
            task (SayouTask): The task definition containing the URI and params.

        Returns:
            SayouPacket: Packet with fetched data on success, or error details
                         on permanent failure.
        """
        self._emit("on_start", input_data=task)
        self._log(f"Fetching: {task.uri} ({task.source_type})", level="debug")

        last_exc: Exception = None

        for attempt in range(1, self.FETCH_MAX_RETRIES + 1):
            try:
                data = self._do_fetch(task)
                packet = SayouPacket(task=task, data=data, success=True)
                self._emit("on_finish", result_data=packet, success=True)
                return packet

            except Exception as e:
                last_exc = e
                if attempt < self.FETCH_MAX_RETRIES:
                    self._log(
                        f"Fetch attempt {attempt}/{self.FETCH_MAX_RETRIES} failed "
                        f"({e}). Retrying in {self.FETCH_RETRY_DELAY}s.",
                        level="warning",
                    )
                    sleep(self.FETCH_RETRY_DELAY)
                else:
                    self._log(
                        f"Fetch failed after {self.FETCH_MAX_RETRIES} attempts: {e}",
                        level="error",
                    )

        self._emit("on_error", error=last_exc)
        wrapped_error = FetcherError(
            f"[{self.component_name}] Failed to fetch: {last_exc}"
        )
        self.logger.error(wrapped_error, exc_info=True)

        return SayouPacket(
            task=task, data=None, success=False, error=str(wrapped_error)
        )

    @abstractmethod
    def _do_fetch(self, task: SayouTask) -> Any:
        """
        [Abstract Hook] Implement the actual data retrieval logic here.

        Args:
            task (SayouTask): The task containing source URI and params.

        Returns:
            Any: The raw data retrieved (e.g., bytes, str, list).

        Raises:
            Exception: Raise any exception if retrieval fails.
                        The parent ``fetch`` method will catch, retry, and wrap it.
        """
        raise NotImplementedError
