"""
System tests for Job.recreate - deletes and recreates a job preserving config.
"""

import logging
import pytest
from jenkinsapi.job import Job
from jenkinsapi_tests.test_utils.random_strings import random_string
from jenkinsapi_tests.systests.job_configs import SHORTISH_JOB

log = logging.getLogger(__name__)

pytestmark = pytest.mark.docker


def test_recreate_job_preserves_config(jenkins):
    """Recreate a job and verify it still exists with the same config."""
    job_name = random_string()
    original_job = jenkins.create_job(job_name, SHORTISH_JOB)
    original_config = original_job.get_config()

    new_job = original_job.recreate()

    assert isinstance(new_job, Job)
    assert new_job.name == job_name
    assert jenkins.has_job(job_name)

    new_config = new_job.get_config()
    # Core config should be preserved (strip whitespace differences)
    assert new_config.strip() == original_config.strip()


def test_recreate_job_resets_build_history(jenkins):
    """Recreate should reset build number to 1."""
    job_name = random_string()
    job = jenkins.create_job(job_name, SHORTISH_JOB)

    qi = job.invoke(block=True)
    assert job.get_last_buildnumber() >= 1

    new_job = job.recreate()
    assert new_job.get_next_build_number() == 1
