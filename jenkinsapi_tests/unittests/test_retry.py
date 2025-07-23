from contextlib import ExitStack
from unittest import mock

import pytest

from jenkinsapi.utils.retry import RetryConfig, RetryState, SimpleRetryConfig


def validate_retry_check(
    retry_config: RetryConfig,
    pass_index: int,
    expected_sleep_count: int,
    expected_pass: bool = True,
) -> None:
    """Check if the retry check works as expected."""
    attempt_index = 0
    success = False
    with ExitStack() as exit_stack:
        exit_stack.enter_context(
            mock.patch("time.monotonic", side_effect=range(100, 1000))
        )
        mock_sleep = exit_stack.enter_context(mock.patch("time.sleep"))
        if not expected_pass:
            exit_stack.enter_context(pytest.raises(TimeoutError))
        retry_state = retry_config.begin()
        assert isinstance(retry_state, RetryState)
        while True:
            attempt_index += 1
            if attempt_index >= pass_index:
                success = True
                break
            retry_state.check_retry()
    if expected_pass:
        assert success
    else:
        assert success is False
    assert mock_sleep.call_count == expected_sleep_count


def test_simple_retry_check():
    retry_config = SimpleRetryConfig(sleep_period=1, timeout=5)
    validate_retry_check(
        retry_config,
        pass_index=3,
        expected_sleep_count=2,
        expected_pass=True,
    )


def test_simple_retry_check_fail():
    retry_config = SimpleRetryConfig(sleep_period=1, timeout=5)
    validate_retry_check(
        retry_config,
        pass_index=10,
        expected_sleep_count=5,
        expected_pass=False,
    )


def test_repr():
    retry_config = SimpleRetryConfig(sleep_period=1, timeout=5)
    assert repr(retry_config) == "SimpleRetryConfig(sleep_period=1, timeout=5)"
