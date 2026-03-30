import functools
import logging
import time
from typing import Any, Callable

logger = logging.getLogger("sayou.core")


def measure_time(func: Callable) -> Callable:
    """
    Measure and log the wall-clock execution time of the decorated function.

    The elapsed time is emitted at DEBUG level so it is invisible in normal
    operation and only surfaces when the application enables debug logging.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - start
            logger.debug("[Timer] %s took %.4fs", func.__qualname__, elapsed)

    return wrapper


def safe_run(default_return: Any = None) -> Callable:
    """
    Prevent a single component failure from crashing the entire pipeline.

    On exception, logs the error at ERROR level and returns ``default_return``
    instead of propagating.  Use sparingly — only on optional / non-critical
    methods such as ``initialize()`` where a failure should be tolerated.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                logger.error(
                    "[SafeRun] Error in %s: %s",
                    func.__qualname__,
                    exc,
                    exc_info=True,
                )
                return default_return

        return wrapper

    return decorator


def retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
) -> Callable:
    """
    Retry a function on failure with exponential back-off.

    Args:
        max_retries: Maximum number of attempts (default 3).
        delay: Initial wait between attempts in seconds (default 1.0).
        backoff: Multiplier applied to ``delay`` after each failure
                 (default 2.0 → 1 s → 2 s → 4 s …).

    Raises:
        The last exception raised if all attempts are exhausted.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc: Exception | None = None
            current_delay = delay

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    logger.warning(
                        "[Retry] %s failed (%d/%d). Retrying in %.1fs…",
                        func.__qualname__,
                        attempt + 1,
                        max_retries,
                        current_delay,
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff

            logger.error(
                "[Retry] %s failed after %d attempts.", func.__qualname__, max_retries
            )
            raise last_exc

        return wrapper

    return decorator
