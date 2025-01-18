"""
System tests for setting jenkins in quietDown mode
"""

import logging


log = logging.getLogger(__name__)


def test_quiet_down_and_cancel_quiet_down(jenkins):
    jenkins.poll()  # jenkins should be alive

    jenkins.quiet_down()  # put Jenkins in quietDown mode
    # is_quieting_down = jenkins.is_quieting_down
    assert jenkins.is_quieting_down is True

    jenkins.poll()  # jenkins should be alive

    jenkins.cancel_quiet_down()  # leave quietDown mode

    # is_quieting_down = jenkins_api['quietingDown']
    assert jenkins.is_quieting_down is False

    jenkins.poll()  # jenkins should be alive
