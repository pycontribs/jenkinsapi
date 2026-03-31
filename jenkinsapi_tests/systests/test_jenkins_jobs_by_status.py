"""
System tests for Jenkins.get_jobs_by_status.
"""

import logging
import pytest
from jenkinsapi.job import Job
from jenkinsapi_tests.test_utils.random_strings import random_string
from jenkinsapi_tests.systests.job_configs import SHORTISH_JOB, EMPTY_JOB

log = logging.getLogger(__name__)

pytestmark = pytest.mark.docker


def test_get_jobs_by_status_success(jenkins):
    """A completed successful job should appear under 'success' status."""
    job_name = random_string()
    job = jenkins.create_job(job_name, SHORTISH_JOB)
    job.invoke(block=True)

    success_jobs = jenkins.get_jobs_by_status("success")

    assert any(isinstance(j, Job) for j in success_jobs)
    names = [j.name for j in success_jobs]
    assert job_name in names


def test_get_jobs_by_status_returns_list(jenkins):
    """get_jobs_by_status always returns a list."""
    result = jenkins.get_jobs_by_status("success")
    assert isinstance(result, list)


def test_get_jobs_by_status_disabled(jenkins):
    """A disabled job should appear under 'disabled' status."""
    job_name = random_string()
    job = jenkins.create_job(job_name, EMPTY_JOB)
    job.disable()

    disabled_jobs = jenkins.get_jobs_by_status("disabled")
    names = [j.name for j in disabled_jobs]
    assert job_name in names
