"""
System tests for setting jenkins in quietDown mode
"""

import time
import logging


log = logging.getLogger(__name__)


def test_quiet_down_and_cancel_quiet_down(jenkins):
    # Retry with exponential backoff for transient connection failures
    max_retries = 5
    retry_delay = 1
    last_error = None
    for attempt in range(max_retries):
        try:
            jenkins.poll()  # jenkins should be alive

            jenkins.quiet_down()  # put Jenkins in quietDown mode
            # is_quieting_down = jenkins.is_quieting_down
            assert jenkins.is_quieting_down is True

            jenkins.poll()  # jenkins should be alive

            jenkins.cancel_quiet_down()  # leave quietDown mode

            # is_quieting_down = jenkins_api['quietingDown']
            assert jenkins.is_quieting_down is False

            jenkins.poll()  # jenkins should be alive
            return
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay = min(
                    retry_delay * 1.5, 5
                )  # exponential backoff, capped at 5s

    raise last_error
