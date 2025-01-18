"""
System tests for `jenkinsapi.jenkins` module.
"""

import time
import logging
from jenkinsapi.build import Build
from jenkinsapi_tests.test_utils.random_strings import random_string
from jenkinsapi_tests.systests.job_configs import LONG_RUNNING_JOB


log = logging.getLogger(__name__)


def test_safe_exit(jenkins):
    job_name = "Bcreate_%s" % random_string()
    job = jenkins.create_job(job_name, LONG_RUNNING_JOB)
    qq = job.invoke()
    time.sleep(3)
    bn = qq.block_until_building(delay=3).get_number()
    assert isinstance(bn, int)

    build = qq.get_build()
    assert isinstance(build, Build)
    assert build.is_running()

    # A job is now running and safe_exit should await running jobs
    # Call, but wait only for 5 seconds then cancel exit
    jenkins.safe_exit(wait_for_exit=False)
    time.sleep(5)

    jenkins.cancel_quiet_down()  # leave quietDown mode
    assert jenkins.is_quieting_down is False

    build.stop()
    # if we call next line right away - Jenkins have no time to stop job
    # so we wait a bit
    while build.is_running():
        time.sleep(0.5)

    console = build.get_console()
    assert isinstance(console, str)
    assert "Started by user" in console
