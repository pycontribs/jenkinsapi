"""
System tests for Job.wipe_out_workspace and Job.trigger_scm_poll.
"""

import logging
import pytest
from jenkinsapi_tests.test_utils.random_strings import random_string
from jenkinsapi_tests.systests.job_configs import SHORTISH_JOB, EMPTY_JOB

log = logging.getLogger(__name__)

pytestmark = pytest.mark.docker


def test_wipe_out_workspace(jenkins):
    """Wipe workspace after a completed build - should not raise."""
    job_name = random_string()
    job = jenkins.create_job(job_name, SHORTISH_JOB)
    job.invoke(block=True)
    # Workspace should now exist; wipe it
    job.wipe_out_workspace()


def test_trigger_scm_poll(jenkins):
    """Trigger an SCM poll on a job - should not raise."""
    job_name = random_string()
    jenkins.create_job(job_name, EMPTY_JOB)
    job = jenkins[job_name]
    job.trigger_scm_poll()
