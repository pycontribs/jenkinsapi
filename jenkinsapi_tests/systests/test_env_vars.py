"""
System tests for `jenkinsapi.jenkins` module.
"""

import time
import pytest
from jenkinsapi_tests.test_utils.retry import retry

from jenkinsapi_tests.systests.job_configs import JOB_WITH_ENV_VARS
from jenkinsapi_tests.test_utils.random_strings import random_string

pytestmark = pytest.mark.docker


@retry(max_attempts=20, initial_delay=0.5)
def test_get_env_vars(jenkins):
    job_name = "get_env_vars_create1_%s" % random_string()
    job = jenkins.create_job(job_name, JOB_WITH_ENV_VARS)
    job.invoke(block=True)
    build = job.get_last_build()
    while build.is_running():
        time.sleep(0.25)

    # Poll for environment variables with exponential backoff
    # Jenkins takes variable time to write injected env vars to API
    data = build.get_env_vars()
    assert data["key1"] == "value1"
    assert data["key2"] == "value2"
