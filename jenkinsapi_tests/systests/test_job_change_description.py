"""
System tests for Job.change_description.
"""

import logging
import pytest
from jenkinsapi_tests.test_utils.random_strings import random_string
from jenkinsapi_tests.systests.job_configs import EMPTY_JOB

log = logging.getLogger(__name__)

pytestmark = pytest.mark.docker


def test_change_description(jenkins):
    """Change job description and verify via get_config."""
    job_name = random_string()
    job = jenkins.create_job(job_name, EMPTY_JOB)

    job.change_description("my new description")

    config = job.get_config()
    assert "<description>my new description</description>" in config


def test_change_description_overwrite(jenkins):
    """Overwrite an existing description."""
    job_name = random_string()
    job = jenkins.create_job(job_name, EMPTY_JOB)

    job.change_description("first")
    job.change_description("second")

    config = job.get_config()
    assert "<description>second</description>" in config
    assert "<description>first</description>" not in config
