"""
System tests for Pipeline input action methods on Build.
"""

import time
import logging
import pytest
from jenkinsapi_tests.test_utils.random_strings import random_string
from jenkinsapi_tests.systests.job_configs import PIPELINE_INPUT_JOB

log = logging.getLogger(__name__)

pytestmark = pytest.mark.docker


def _wait_for_input(build, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            actions = build.get_pending_input_actions()
            if actions:
                return actions
        except Exception:
            pass
        time.sleep(2)
    return []


def test_get_pending_input_actions(jenkins):
    job_name = "input_%s" % random_string()
    job = jenkins.create_job(job_name, PIPELINE_INPUT_JOB)
    qq = job.invoke()
    qq.block_until_building()
    build = qq.get_build()

    actions = _wait_for_input(build)
    assert len(actions) >= 1
    input_id = actions[0]["id"]
    assert input_id.lower() == "deploy-approval"
    assert "Deploy to production?" in actions[0]["message"]

    # Clean up — abort so build doesn't hang
    build.abort_input(input_id)


def test_proceed_input(jenkins):
    job_name = "proceed_%s" % random_string()
    job = jenkins.create_job(job_name, PIPELINE_INPUT_JOB)
    qq = job.invoke()
    qq.block_until_building()
    build = qq.get_build()

    actions = _wait_for_input(build)
    assert actions
    input_id = actions[0]["id"]

    build.proceed_input(input_id)

    deadline = time.time() + 30
    while time.time() < deadline and build.is_running():
        time.sleep(2)

    assert not build.is_running()


def test_abort_input(jenkins):
    job_name = "abort_%s" % random_string()
    job = jenkins.create_job(job_name, PIPELINE_INPUT_JOB)
    qq = job.invoke()
    qq.block_until_building()
    build = qq.get_build()

    actions = _wait_for_input(build)
    assert actions
    input_id = actions[0]["id"]

    build.abort_input(input_id)

    deadline = time.time() + 30
    while time.time() < deadline and build.is_running():
        time.sleep(2)

    assert not build.is_running()
