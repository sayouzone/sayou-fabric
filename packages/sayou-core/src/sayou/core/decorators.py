import time
import logging
import functools
from typing import Callable, Any

logger = logging.getLogger("SayouCore")

def measure_time(func: Callable) -> Callable:
    """
    [Decorator] 함수 실행 시간을 측정하여 로그로 남깁니다.
    성능 병목 구간을 찾을 때 유용합니다.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.perf_counter()
            elapsed = end_time - start_time
            logger.debug(f"[Timer] {func.__qualname__} took {elapsed:.4f}s")
    return wrapper

def safe_run(default_return: Any = None) -> Callable:
    """
    [Decorator] 에러가 발생해도 파이프라인을 죽이지 않고, 
    로그를 남긴 뒤 기본값(default_return)을 반환합니다.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"[SafeRun] Error in {func.__qualname__}: {e}", exc_info=True)
                return default_return
        return wrapper
    return decorator

def retry(max_retries: int = 3, delay: float = 1.0) -> Callable:
    """
    [Decorator] 실패 시 일정 횟수만큼 재시도합니다.
    네트워크 요청(Connector, LLM)에 필수적입니다.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"[Retry] {func.__qualname__} failed ({attempt+1}/{max_retries}). Retrying in {delay}s...")
                    time.sleep(delay)
            
            logger.error(f"[Retry] {func.__qualname__} failed after {max_retries} attempts.")
            raise last_exception
        return wrapper
    return decorator