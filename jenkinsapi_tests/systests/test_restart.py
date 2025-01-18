"""
System tests for restarting jenkins

NB: this test will be very time consuming because
    after restart it will wait for jenkins to boot
"""

import time
import logging
import pytest
from requests import HTTPError, ConnectionError

log = logging.getLogger(__name__)


def wait_for_restart(jenkins):
    wait = 15
    count = 0
    max_count = 30
    success = False
    msg = (
        "Jenkins has not restarted yet! (This is try %s of %s, "
        "waited %s seconds so far) "
        "Sleeping %s seconds and trying again..."
    )

    while count < max_count or not success:
        time.sleep(wait)
        try:
            jenkins.poll()
            log.info("Jenkins restarted successfully.")
            success = True
            break
        except HTTPError as ex:
            log.info(ex)
        except ConnectionError as ex:
            log.info(ex)

        log.info(msg, count + 1, max_count, count * wait, wait)
        count += 1

    if not success:
        msg = (
            "Jenkins did not come back from safe restart! "
            "Waited {0} seconds altogether.  This "
            "failure may cause other failures."
        )
        log.critical(msg.format(count * wait))
        pytest.fail(msg)


def test_safe_restart_wait(jenkins):
    jenkins.poll()  # jenkins should be alive
    jenkins.safe_restart()  # restart and wait for reboot (default)
    jenkins.poll()  # jenkins should be alive again


def test_safe_restart_dont_wait(jenkins):
    jenkins.poll()  # jenkins should be alive
    jenkins.safe_restart(wait_for_reboot=False)
    # Jenkins sleeps for 10 seconds before actually restarting
    time.sleep(11)
    with pytest.raises((HTTPError, ConnectionError)):
        # this is a 503: jenkins is still restarting
        jenkins.poll()
    # the test is now complete, but other tests cannot run until
    # jenkins has finished restarted.  to avoid cascading failure
    # we have to wait for reboot to finish.
    wait_for_restart(jenkins)
