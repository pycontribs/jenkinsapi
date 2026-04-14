"""Retry decorator with exponential backoff for resilient tests."""

import functools
import time
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def retry(
    max_attempts: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 5.0,
    backoff_multiplier: float = 1.5,
) -> Callable:
    """
    Decorator that retries a function with exponential backoff.

    Useful for system tests that experience transient failures (e.g., connection errors).

    Args:
        max_attempts: Maximum number of attempts (default: 5)
        initial_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay between retries, capped (default: 5.0)
        backoff_multiplier: Multiplier for exponential backoff (default: 1.5)

    Example:
        @retry()
        def test_something(jenkins):
            # test logic
            pass

        @retry(max_attempts=3, initial_delay=0.5)
        def test_something_else(jenkins):
            # test logic
            pass
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_error = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
                        delay = min(delay * backoff_multiplier, max_delay)

            raise last_error

        return wrapper

    return decorator
