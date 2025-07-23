import time
from abc import ABC, abstractmethod
from dataclasses import dataclass


class RetryConfig(ABC):
    """
    Base class for retry configuration

    Usage::

        retry_check = retry_config.begin()
        while True:
            result = try_something()
            if result:
                return result
            retry_check.check_retry()

    All state is stored in the `RetryCheck` instance so `RetryConfig` can be
    used in multiple contexts simultaneously.
    """

    @abstractmethod
    def begin(self) -> "RetryState": ...


class RetryState(ABC):
    """
    Base class for limited retry checks
    """

    @abstractmethod
    def check_retry(self) -> None:
        """Sleep or raise `TimeoutError`"""
        pass


@dataclass
class SimpleRetryConfig(RetryConfig):
    sleep_period: float = 1
    timeout: float = 5

    def begin(self) -> "SimpleRetryState":
        return SimpleRetryState(self)


@dataclass
class SimpleRetryState(RetryState):
    """Basic implementation of RetryCheck with fixed sleep and timeout."""

    config: SimpleRetryConfig
    start_time: float

    def get_current_time(self) -> float:
        return time.monotonic()

    def __init__(self, config: SimpleRetryConfig):
        self.config = config
        self.start_time = self.get_current_time()

    def check_retry(self) -> None:
        curr_time = self.get_current_time()
        if curr_time - self.start_time > self.config.timeout:
            raise TimeoutError("Retry timed out")
        time.sleep(self.config.sleep_period)
